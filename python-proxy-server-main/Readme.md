# Forward proxy server

## Introduction
In computer networks, A proxy server is a server ( A computer system or
an application ) that acts as an intermediary for requests from clients
seeking resources from other servers. A client connects to the proxy
server, requesting some service, such as a file, connection, web page,
or other resource available from a different server and the proxy server
evaluates the request as a way to simplify and control its complexity.

Proxies were invented to add structure and encapsulation to distributed
systems. Today, most proxies are web proxies, facilitating access to
content on the World Wide Web and providing anonymity.

### illustration
<p align ="left">
<img src= "assets/proxy-illustration.jpg" alt="Basic proxy understanding">
</p>
What Bob thinks is the server ( i.e the proxy ) asked for the current time, But what Bob didn't know was, Alice asked for the current time but through the proxy server. The proxy server returns the current time to Alice. So we can basically say, Server Bob has been tricked. The proxy server acts as a man in the middle serving two people without revealing their identities to each other, Each person sees only the proxy but not the other end.

Uses:
1. Filtering of encrypted data
2. Bypassing filters and censorship
3. Logging and eavesdropping
4. Improving performance
5. Security
6. Cross-domain resources
7. Translation
8. Anonymity

## Run

* Bare Metal

```
python3 src/server.py --max_conn=10 --buffer_size=8192
```

* Container

```
docker run -p 8000:5000 -it python-proxy-server
```
## Screenshot
<p align = "left">
<img src= "assets/screenshot.png" alt ="screenshot" width="65%" height= "65%">
</p>

## Deployment
Can be deployed on [Heroku](https://www.heroku.com) using official [Python buildpack](https://github.com/heroku/heroku-buildpack-python) and [QuotaGuard Static](https://elements.heroku.com/addons/quotaguardstatic) add-on for a static runtime environment.

## Setup and Testing
If running the proxy on your local machine with the above example, point your proxy to;
```localhost 8000```

Test access to a HTTP only webpage such as;
```http://neverssl.com```

NB: This proxy only works with HTTP connections, HTTPS will not work.