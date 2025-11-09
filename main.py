import wifi  # type: ignore
import socketpool  # type: ignore
import time
import usb_hid  # type: ignore
import json
from adafruit_hid.mouse import Mouse  # type: ignore

HTML_PAGE = """<style>
    #tap {
        width: 100%;
        height: 100%;
        background-color: rgb(255, 255, 255);
        margin: none;
        padding: none;
        touch-action: none;
        user-select: none;
        position: absolute;
    }
    body {
        overflow: hidden;
    }
    #newDrawing {
        /* align-self: flex-end; */
        border-style: none;
        border-radius: 1rem;
        position: fixed;
        right: 5%;
        bottom: 5%;
        aspect-ratio: 5/2;
        width: clamp(1px, 30%, 200px);
        /* height: 15%; */
        font-size: clamp(1px, 2vw, 100px);

        z-index: 1000;
        background-color: rgb(40, 144, 40);
        color: white;
        padding: 0.7rem;
        transition: all 0.2s;
    }
    #newDrawing:hover {
        background-color: rgb(71, 160, 71);
        transform: scale(1.1) rotate(2deg);
    }
</style>
<h1>
    <h1 id="coords">Tap anywhere</h1>
    <canvas id="tap"></canvas>
    <button type="button" id="newDrawing" onclick="newDrawing()">
        New Drawing
    </button>
</h1>

<script>
    const canvas = document.getElementById("tap");
    const ctx = canvas.getContext("2d");
    canvas.width = window.innerWidth * 0.9;
    canvas.height = window.innerHeight * 0.7;
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    SCALE = 0.25;

    let screenInfo = {
        width: window.innerWidth,
        height: window.innerHeight,
    };

    let points = [["New", "New"]];
    let clicked = false;

    let lastX = 0;
    let lastY = 0;
    let x,
        y = 0;
    function addMouseUp() {
        if (points[points.length - 3] != "False") {
            points.push(["False", "False"]);
        }
    }
    function newDrawing() {
        location.reload();
    }
    canvas.addEventListener("mousedown", (e) => {
        lastX = x;
        lastY = y;
        addMouseUp();
        clicked = true;
    });
    canvas.addEventListener("mouseup", (e) => {
        e.preventDefault();
        clicked = false;
        addMouseUp();
    });
    canvas.addEventListener("touchstart", (e) => {
        lastX = x;
        lastY = y;

        addMouseUp();
        clicked = true;
    });
    canvas.addEventListener("touchend", (e) => {
        e.preventDefault();
        clicked = false;
        addMouseUp();
    });
    canvas.addEventListener("touchmove", (e) => {
        draw(e);
    });

    canvas.addEventListener("mousemove", (e) => {
        draw(e);
    });
    function draw(e) {
        if (!clicked) return;
        e.preventDefault();
        const rect = canvas.getBoundingClientRect();
        let x, y;
        if (e.touches && e.touches[0]) {
            x = e.touches[0].clientX - rect.left;
            y = e.touches[0].clientY - rect.top;
        } else {
            x = e.clientX - rect.left;
            y = e.clientY - rect.top;
        }

        ctx.strokeStyle = "black";
        ctx.lineWidth = 12;
        ctx.lineCap = "round";

        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(x, y);
        ctx.stroke();

        lastX = x;
        lastY = y;

        points.push([x / 2, y / 2]);
    }

    setInterval(() => {
        if (points.length > 0) {
            fetch("/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Connection: "close",
                },

                body: JSON.stringify(points),
            });
            points = [];
        }
    }, 2500);
    // }
</script>

"""


def read_full_request(conn):
    temp = bytearray(1024)
    data = bytearray()
    content_len = 0
    have_headers = False

    while True:
        try:
            n = conn.recv_into(temp)
        except OSError as e:
            print("Timeout")
            break

        if n == 0:
            break

        data.extend(temp[:n])

        if not have_headers and b"\r\n\r\n" in data:
            have_headers = True
            header, body = data.split(b"\r\n\r\n", 1)
            for line in header.split(b"\r\n"):
                if line.lower().startswith(b"content-length:"):
                    content_len = int(line.split(b":", 1)[1].strip())
                    break
            if content_len == 0:
                break

        if have_headers and len(body) >= content_len:
            break

    return bytes(data)


offsetX = 0
offsetY = 0
points = []
currentX = 0
currentY = 0


def next():
    global offsetX, offsetY, points, conn, addr, currentY, currentX
    pool = socketpool.SocketPool(wifi.radio)
    server = pool.socket()
    server.bind(("", 80))
    server.listen(1)
    print("Listening on http://%s" % wifi.radio.ipv4_address)
    server.settimeout(0.1)
    try:
        while True:
            try:
                conn, addr = server.accept()
                conn.settimeout(2)

                # buffer = bytearray(16384)
                # size = conn.recv_into(buffer)
                request = read_full_request(conn)
                request_str = request.decode()
                if "POST" in request_str:
                    print("post")
                    print(request)
                    parts = request.split(b"\r\n\r\n", 1)
                    if len(parts) > 1:
                        body = parts[1] if len(parts) > 1 else b""
                        try:
                            newpoints = json.loads(body)
                            points += newpoints
                        except:
                            print("failed")

                else:
                    print("Get")
                    response = (
                        "HTTP/1.1 200 OK\r\n"
                        "Content-Type: text/html\r\n"
                        "Connection: close\r\n"
                        "\r\n" + HTML_PAGE
                    )
                    conn.send(response.encode())
                conn.close()
            except:
                pass
            time.sleep(0.05)
            if len(points) > 0:
                try:
                    print("Got", len(points), "points")
                    newx = points[0][0]
                    newy = points[0][1]

                    if newx == "New":
                        offsetX = 0
                        offsetY = 0
                        currentX = 0
                        currentY = 0

                    elif newx == "False":
                        if len(points) >= 2 and currentY != 0:
                            mouse.release(Mouse.LEFT_BUTTON)
                            offsetY += (currentY - offsetY - points[2][1]) / 2 - 5
                            offsetX += (currentX - offsetX - points[2][0]) / 2 - 4

                            points.pop(0)
                    else:
                        if (
                            offsetX == 0
                            and offsetY == 0
                            and currentX == 0
                            and currentY == 0
                        ):
                            offsetX = -newx
                            offsetY = -newy
                            print("reset offset for new stroke")

                        mouse.move(
                            x=round(newx - currentX + offsetX),
                            y=round(newy - currentY + offsetY),
                        )
                        mouse.press(Mouse.LEFT_BUTTON)
                        currentX = newx + offsetX
                        currentY = newy + offsetY

                    points.pop(0)
                except Exception as e:
                    points = []
                    print("json parse fail", e)
            else:
                mouse.release(Mouse.LEFT_BUTTON)
    except KeyboardInterrupt:
        print("Stopped")
    finally:
        server.close()
        wifi.radio.enabled = False
        print("Closed")


mouse = Mouse(usb_hid.devices)
print("Hello!")
ssid = "Wifi Here"
password = "Password Here"
wifi.radio.enabled = True
time.sleep(1)
print("Connecting to WiFi...")
try:
    wifi.radio.connect(ssid, password)
    next()
finally:
    # server.close()
    wifi.radio.enabled = False
    print("Closed")

print("✅ Connected to", ssid)
print("IP:", wifi.radio.ipv4_address)
