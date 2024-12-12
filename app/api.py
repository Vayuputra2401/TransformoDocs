from fastapi import FastAPI, File, UploadFile, HTTPException, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
import time
import datetime
from extractor import validate_document, extract_text_with_size
from processor import process_document
import logging
import io
from collections import defaultdict
from typing import Dict

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "a_very_strong_secret_key_that_should_be_kept_private"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

request_count = 0
total_latency = 0

# Rate limiting configuration
RATE_LIMIT = 5  # Number of requests per second
rate_limit_window = 1  # Time window in seconds
client_requests: Dict[str, list] = defaultdict(list)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_access_token(data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def rate_limiter(client_id: str):
    current_time = time.time()
    request_times = client_requests[client_id]

    # Remove outdated requests
    while request_times and request_times[0] < current_time - rate_limit_window:
        request_times.pop(0)

    if len(request_times) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    request_times.append(current_time)

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
    request: Request ,
    file: UploadFile = File(...), 
    token: str = Depends(verify_token)
):
    global request_count, total_latency
    start_time = time.time()
    client_id = request.client.host
    rate_limiter(client_id)
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
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        # Here you should verify the username and password
        # For demonstration, we assume the username is "user" and password is "password"
        if form_data.username == "user" and form_data.password == "password":
            access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": form_data.username}, expires_delta=access_token_expires
            )
            return {"access_token": access_token, "token_type": "bearer"}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password")
    except Exception as e:
        logger.error(f"Error generating token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats(token: str = Depends(verify_token)):
    global request_count, total_latency
    try:
        avg_latency = total_latency / request_count if request_count > 0 else 0
        return {"request_count": request_count, "average_latency": avg_latency}
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))