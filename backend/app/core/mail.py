from mailjet_rest import Client
from typing import List, Dict
import os
import base64
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MAILJET_API_KEY")
api_secret = os.getenv("MAILJET_SECRET_KEY")
sender_email = os.getenv("SENDER_EMAIL")
sender_name = os.getenv("SENDER_NAME")

if api_key is None or api_secret is None:
    raise ValueError("MAILJET_API_KEY and MAILJET_SECRET_KEY must be set in environment variables.")

mailjet = Client(auth=(api_key, api_secret), version='v3.1')

def send_html_email(to_email: str, to_name: str, subject: str, html_content: List[Dict], inline_images: list = []):
    """
    Send an HTML email using Mailjet with optional inline images.
    inline_images: list of dicts with keys: "ContentID", "ContentType", "Filename", "Base64Content"
    """
    html, images = render_html_email(html_content)
    
    message = {
        "Messages": [
            {
                "From": {
                    "Email": sender_email,
                    "Name": sender_name
                },
                "To": [{
                    "Email": to_email,
                    "Name": to_name
                }],
                "Subject": subject,
                "HTMLPart": html,
                "InlineAttachments": images
            }
        ]
    }

    result = mailjet.send.create(data=message)
    return result.json()


def render_block(block: Dict) -> str:
    block_type = block.get("type")
    content: List[Dict] = block.get("content", [])

    if block_type == "table":
        return f"""
        <table role="presentation" cellpadding="0" cellspacing="0" style="font-size:0px;width:100%;" align="center" border="0">
            <tbody>
                <tr>
                    <td style="text-align:center;vertical-align:top;font-size:0px;padding:20px;">
                        <div style="vertical-align:top;display:inline-block;font-size:13px;text-align:left;width:100%">
                            <table role="presentation" cellpadding="0" cellspacing="0" width="100%" border="0">
                                <tbody>
                                    {''.join(render_block(b) for b in content)}
                                </tbody>
                            </table>
                        </div>
                    </td>
                </tr>
            </tbody>
        </table>
        """

    elif block_type == "image":
        return f"""
        <tr>
            <td align="center" style="padding-bottom:30px">
                <img src="{content}" alt="Image" width="180" style="display:block;width:100%;height:auto;border:none;outline:none;">
            </td>
        </tr>
        """

    elif block_type == "header":
        return f"""
        <tr>
            <td align="center" style="padding-bottom:30px">
                <div style="color:#55575d;font-family:Open Sans,Helvetica,Arial,sans-serif;font-size:22px;font-weight:700;line-height:22px">
                    {content}
                </div>
            </td>
        </tr>
        """

    elif block_type == "text":
        # If content is a list of dicts, join their 'content' fields
        if isinstance(content, list):
            text = ''.join(str(item.get("content", "")) for item in content)
        else:
            text = str(content)
        return f"""
        <tr>
            <td align="center" style="padding-bottom:15px">
                <div style="color:#8c8c8c;font-family:Roboto,Helvetica,Arial,sans-serif;font-size:14px;line-height:22px">
                    {text.replace("break-line", "<br>")}
                </div>
            </td>
        </tr>
        """

    elif block_type == "html":
        return f"""
        <tr>
            <td align="center" style="padding-bottom:10px">
                {content}
            </td>
        </tr>
        """

    elif block_type == "list":
        links = " | ".join([
            f'<a href="{item.get("link", "#")}" style="text-decoration:none;color:#8c8c8c;margin:0 5px;">{item["content"]}</a>'
            for item in content
        ])
        return f"""
        <tr>
            <td align="center" style="padding-bottom:15px">
                <div style="font-size:12px;font-family:Roboto,Helvetica,Arial,sans-serif;line-height:22px">{links}</div>
            </td>
        </tr>
        """

    elif block_type == "hyperlink":
        return f'<a href="{block.get("link", "#")}">{block["content"]}</a>'
    
    elif block_type == "button":
        return f'<a href="{block.get("link", "#")} style="{block.get("content", "display: inline-block;padding: 6px 12px;margin-bottom: 2px;font-size: inherit;font-weight: 400;line-height: 1.42857143;text-align: center;white-space: nowrap;vertical-align: middle;-ms-touch-action: manipulation;touch-action: manipulation;cursor: pointer;-webkit-user-select: none;-moz-user-select: none;-ms-user-select: none;user-select: none;background-image: none;border: 1px solid transparent;border-radius: 4px;background-color: rgb(33, 150, 243);color: rgb(255, 255, 255)")}">{block["content"]}</a>'

    return ""

def encode_image_as_base64(file_path: str):
    with open(file_path, "rb") as img:
        b64 = base64.b64encode(img.read()).decode("utf-8")
    return b64

def extract_image_sources_from_json(content: list) -> list:
    image_sources = []

    def walk(blocks):
        for block  in blocks:
            block_type = block.get("type")
            if block_type == "image":
                image_sources[block["content"]]
            elif block_type in ["table", "list"]:
                walk(block.get("content", []))

    walk(content)

    return image_sources

def render_html_email(content: List[Dict]) -> Dict:
    body = ''.join(render_block(block) for block in content)
    images = extract_image_sources_from_json(content)
    html = f"""
    <div style="background:#f5f5f5;padding-top:80px">
        <div style="margin:0 auto;max-width:600px;background:#ffffff;border-top:3px solid #6f67d9">
            {body}
        </div>
    </div>
    """
    
    return parse_html_with_image(html, images)


def parse_html_with_image(html: str, images: list) -> Dict:
    inline_images = []

    for image in images:
        image_b64 = encode_image_as_base64(image)
        filename = image.split("/")[len(image.split("/")) - 1]
        image_id = f"{filename.split(".")[0]}_cid"
        inline_images.append({
            "ContentType": "image/png",
            "Filename": filename,
            "ContentID": image_id,
            "Base64Content": image_b64
        })

        html.replace(image, f"cid:{image_id}")


    return {"html": html, "image": inline_images}