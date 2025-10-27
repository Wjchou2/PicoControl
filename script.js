let device;
const statusLabel = document.getElementById("status");
let rxCharacteristic, service;

async function connectBLE() {
    device = await navigator.bluetooth.requestDevice({
        // acceptAllDevices: true,
        filters: [{ services: ["6e400001-b5a3-f393-e0a9-e50e24dcca9e"] }],
    });
    device.addEventListener("gattserverdisconnected", () => {
        statusLabel.innerHTML = "❌ Disconnected";
    });
    const server = await device.gatt.connect();
    service = await server.getPrimaryService(
        "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
    );

    rxCharacteristic = await service.getCharacteristic(
        "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
    );
    statusLabel.innerHTML = "✅ Connected";
}

document.getElementById("send").addEventListener("click", async () => {
    if (!rxCharacteristic) {
        alert("Not connected!");
        return;
    }

    const text = "Hello from phone!";
    const encoder = new TextEncoder();
    await rxCharacteristic.writeValue(encoder.encode(text + "\n"));
    console.log("📤 Sent:", text);
});
