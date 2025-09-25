package perf;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;

import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;
import java.util.stream.Stream;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

public class RestfulBookerCrudSimulation extends Simulation {

    private final String baseUrl   = System.getProperty("baseUrl", "https://restful-booker.herokuapp.com");
    private final int durationSec  = Integer.parseInt(System.getProperty("durationSec", "120"));
    private final int rampUsers    = Integer.parseInt(System.getProperty("rampUsers", "5"));
    private final int targetRps    = Integer.parseInt(System.getProperty("targetRps", "10"));

    HttpProtocolBuilder httpProtocol =
            http.baseUrl(baseUrl)
                    .contentTypeHeader("application/json")
                    .acceptHeader("application/json");

    // Генератор за booking полиња
    Iterator<Map<String, Object>> bookingFeeder = Stream.generate(() -> {
        var rnd = ThreadLocalRandom.current();
        var start = LocalDate.now().plusDays(rnd.nextInt(1, 10));
        var end   = start.plusDays(rnd.nextInt(1, 5));
        Map<String, Object> m = new HashMap<>();
        m.put("firstname", "User" + rnd.nextInt(100000));
        m.put("lastname",  "Perf" + rnd.nextInt(100000));
        m.put("totalprice", rnd.nextInt(50, 500));
        m.put("depositpaid", rnd.nextBoolean());
        m.put("checkin",  start);
        m.put("checkout", end);
        m.put("needs", rnd.nextBoolean() ? "Breakfast" : "Late checkout");
        return m;
    }).iterator();

    // 1) AUTH → земи token
    ChainBuilder auth =
            exec(
                    http("CreateToken")
                            .post("/auth")
                            .body(StringBody("{\"username\":\"admin\",\"password\":\"password123\"}"))
                            .check(status().is(200))
                            .check(jsonPath("$.token").saveAs("token"))
            );

    // 2) CREATE → зачувај bookingId
    ChainBuilder create =
            feed(bookingFeeder)
                    .exec(
                            http("CreateBooking")
                                    .post("/booking")
                                    .body(StringBody("""
            {
              "firstname": "#{firstname}",
              "lastname": "#{lastname}",
              "totalprice": #{totalprice},
              "depositpaid": #{depositpaid},
              "bookingdates": { "checkin": "#{checkin}", "checkout": "#{checkout}" },
              "additionalneeds": "#{needs}"
            }
          """)).asJson()
                                    .check(status().is(200))
                                    .check(jsonPath("$.bookingid").saveAs("bookingId"))
                    );

    // 3) READ
    ChainBuilder read =
            exec(
                    http("GetBookingById")
                            .get("/booking/#{bookingId}")
                            .check(status().is(200))
                            .check(jsonPath("$.firstname").exists())
            );

    // 4) UPDATE (со Cookie token) – користи нови вредности од feeder
    ChainBuilder update =
            feed(bookingFeeder)
                    .exec(
                            http("UpdateBooking")
                                    .put("/booking/#{bookingId}")
                                    .header("Cookie", "token=#{token}")
                                    .body(StringBody("""
            {
              "firstname": "#{firstname}",
              "lastname": "#{lastname}",
              "totalprice": #{totalprice},
              "depositpaid": #{depositpaid},
              "bookingdates": { "checkin": "#{checkin}", "checkout": "#{checkout}" },
              "additionalneeds": "#{needs}"
            }
          """)).asJson()
                                    .check(status().in(200, 201, 202))
                    );

    // 5) DELETE
    ChainBuilder delete =
            exec(
                    http("DeleteBooking")
                            .delete("/booking/#{bookingId}")
                            .header("Cookie", "token=#{token}")
                            .check(status().in(200, 201, 202, 204))
            );

    // Негативен update со BAD token → 403
    ChainBuilder updateInvalidToken =
            feed(bookingFeeder)
                    .exec(
                            http("UpdateBooking - Invalid Token")
                                    .put("/booking/#{bookingId}")
                                    .header("Cookie", "token=BADTOKEN")
                                    .body(StringBody("""
            {
              "firstname": "#{firstname}",
              "lastname": "#{lastname}",
              "totalprice": #{totalprice},
              "depositpaid": #{depositpaid},
              "bookingdates": { "checkin": "#{checkin}", "checkout": "#{checkout}" },
              "additionalneeds": "#{needs}"
            }
          """)).asJson()
                                    .check(status().is(403))
                    );

    ScenarioBuilder crudHappyPath =
            scenario("CRUD Happy Path").exec(auth, create, read, update, delete);

    ScenarioBuilder crudNegative =
            scenario("CRUD Negative - bad token").exec(auth, create, updateInvalidToken);

    {
        setUp(
                crudHappyPath.injectOpen(rampUsers(rampUsers).during(durationSec)),
                crudNegative.injectOpen(constantUsersPerSec(1).during(30))
        )
                .protocols(httpProtocol)
                .throttle(reachRps(targetRps).in(30), holdFor(durationSec))
                .assertions(
                        global().successfulRequests().percent().gt(98.0),
                        forAll().responseTime().percentile(95).lt(1000)   // <— поправено
                );
    }
}
