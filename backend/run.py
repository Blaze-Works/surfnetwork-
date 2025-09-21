import os;
import uvicorn;
from dotenv import load_dotenv;

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5729))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)