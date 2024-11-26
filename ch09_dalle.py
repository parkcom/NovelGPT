import base64
import io

from openai import OpenAI
from PIL import Image


def get_image_by_dalle(client: OpenAI, genre, img_prompt):
    response = client.images.generate(
        model="dall-e-3",
        prompt="The name of this story is "
        + genre
        + ". "
        + img_prompt
        + """ The style is
    3D computer-rendered children's movie animation with vibrant colors and detailed textures.""",
        size="1024x1024",
        quality="standard",
        n=1,
        response_format="b64_json",
    )

    image_data = base64.b64decode(response.data[0].b64_json)
    image = Image.open(io.BytesIO(image_data))
    return image
