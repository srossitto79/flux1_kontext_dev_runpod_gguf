import requests
import base64
from io import BytesIO

url = "http://localhost:3000/"

base64_input = ""

img_size = None
with open("./test_input2.jpg", "rb") as f:
    img_bytes = f.read()
    #resize the image to 1MPixels
    from PIL import Image
    img = Image.open(f)
    
    #img = img.resize((int((1_000_000 * img.width / img.height) ** 0.5), int((1_000_000 * img.height / img.width) ** 0.5)))
    # Use preferred resolutions from Flux Kontext pipeline
    preferred_resolutions = [
        (672, 1568), (688, 1504), (720, 1456), (752, 1392), (800, 1328), (832, 1248),
        (880, 1184), (944, 1104), (1024, 1024), (1104, 944), (1184, 880), (1248, 832),
        (1328, 800), (1392, 752), (1456, 720), (1504, 688), (1568, 672)
    ]
    w, h = img.size
    aspect_ratio = w / h
    # Find the closest valid resolution by aspect ratio
    _, target_w, target_h = min(
        (abs(aspect_ratio - vw/vh), vw, vh) for vw, vh in preferred_resolutions if vw >= w and vh >= h
    )
    img = img.resize((target_w, target_h), Image.LANCZOS)
    print(f"Resized input image to {target_w}x{target_h}")

    #img.save("resized.png")
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    base64_input = base64.b64encode(img_bytes).decode("utf-8")
    img_size = img.size

payload = {
    "input": {
        "image": base64_input,
        "prompt": "Transform this exterior space, enhancing textures and lighting. Preserve the camera angle, geometry, and composition. Enhance the vibrant colors and detailed textures of the image. Add subtle shadows and highlights to create a more realistic and immersive environment. Preserve the natural atmosphere and the ambiance.",
        "num_inference_steps": 20,
        "guidance_scale": 7.5,
        "width": img_size[0],
        "height": img_size[1]
    }
}

# Send the request
resp = requests.post(url, json=payload)
resp.raise_for_status()

data = resp.json()

if "image_base64" not in data:
    raise ValueError(f"Unexpected response: {data}")

# Decode and save the resulting image
img_b64 = data["image_base64"]
img_bytes = base64.b64decode(img_b64)

with open("result.png", "wb") as f:
    f.write(img_bytes)

print("✅ Image saved to result.png")
