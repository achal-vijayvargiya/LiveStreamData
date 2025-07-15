import asyncio
from ..core.watcher import watch_image_src
from ..ocr.engine import ocr_image_google_vision
from PIL import Image
from ..websocket.data_poster import post_data
from ..core.multi_user_watcher import MultiUserWatcher

async def main():
    
    # # INSERT_YOUR_CODE
    # import os

    # images_dir = "images"
    # if os.path.exists(images_dir):
    #     for filename in os.listdir(images_dir):
    #         if filename.lower().endswith((".png", ".jpg", ".jpeg")):
    #             image_path = os.path.join(images_dir, filename)
    #             text = ocr_image_google_vision(image_path)
    #             print(f"Processing {filename}")
    #             await post_data(text, image_path)
    #     print("done")
    # else:
    #     print(f"Images directory '{images_dir}' does not exist.")
    # # text = ocr_image_google_vision("canvas_capture.png")
    # print(f"text: {text}")
    # await post_data(text)
    # await watch_image_src()
    watcher = MultiUserWatcher("app/config/users.json")
    await watcher.run_all_users()
    

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Shutting down gracefully.') 