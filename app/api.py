from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
import time
import datetime
from extractor import validate_document, extract_text_with_size
from processor import process_document
import logging
import io

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "a_very_strong_secret_key_that_should_be_kept_private"

request_count = 0
total_latency = 0

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


class DocumentResponse(BaseModel):
    structured_data: dict
    analytics: dict
    json_output: str
    xml_output: str
    extracted_text: str
    warnings: list


# Custom file-like object with name attribute
class NamedBytesIO(io.BytesIO):
    def __init__(self, content: bytes, filename: str):
        super().__init__(content)
        self._name = filename

    @property
    def name(self):
        return self._name

    @property
    def size(self):
        return len(self.getvalue())


@app.post("/api/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...), token: str = Depends(verify_token)
):
    global request_count, total_latency
    start_time = time.time()
    try:

        # Read file content
        file_content = await file.read()

        # Determine original filename and fallback filename
        original_filename = file.filename or "uploaded_file"
        if original_filename == "file":
            # Safely handle content_type
            content_type = (
                file.content_type.split("/")[-1] if file.content_type else "unknown"
            )
            extension = f".{content_type}" if content_type != "unknown" else ".bin"
            original_filename = f"uploaded_{int(time.time())}{extension}"

        logger.info(
            f"Received file: {original_filename}, size: {len(file_content)} bytes"
        )

        # Wrap file content in NamedBytesIO
        named_file = NamedBytesIO(file_content, original_filename)

        # Validate file type
        logger.info(f"Validating file: {named_file.name}")
        file_type = validate_document(named_file)
        logger.info(f"File type identified as: {file_type}")

        # Reset file pointer after validation
        named_file.seek(0)

        # Extract text
        extracted_text, file_size = extract_text_with_size(named_file, file_type)
        logger.info(f"Extracted text size: {file_size} bytes")

        # Process document
        result = process_document(extracted_text)
        logger.info("Document processed successfully")

        request_count += 1
        total_latency += time.time() - start_time

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/token")
async def generate_token():
    try:
        token = jwt.encode(
            {"exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
            SECRET_KEY,
            algorithm="HS256",
        )
        return {"token": token}
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    global request_count, total_latency
    try:
        avg_latency = total_latency / request_count if request_count > 0 else 0
        return {"request_count": request_count, "average_latency": avg_latency}
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
