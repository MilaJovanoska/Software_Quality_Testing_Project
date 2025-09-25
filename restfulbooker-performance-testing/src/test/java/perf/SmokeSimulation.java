package perf;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

public class SmokeSimulation extends Simulation {

    private final String baseUrl = System.getProperty("baseUrl", "https://restful-booker.herokuapp.com");

    HttpProtocolBuilder httpProtocol =
            http.baseUrl(baseUrl)
                    .acceptHeader("application/json");

    ScenarioBuilder smoke =
            scenario("Smoke - ping & list ids")
                    .exec(
                            http("Ping")
                                    .get("/ping")
                                    .check(status().in(200, 201))
                    )
                    .exec(
                            http("GetBookingIds")
                                    .get("/booking")
                                    .check(status().is(200))
                    );

    {
        setUp(smoke.injectOpen(atOnceUsers(1)))
                .protocols(httpProtocol)
                .assertions(
                        global().successfulRequests().percent().gt(99.0),
                        global().responseTime().percentile3().lt(800)
                );
    }
}
