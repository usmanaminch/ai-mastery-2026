FROM pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN pip install --no-cache-dir \
    transformers==4.44.0 \
    datasets==2.20.0 \
    peft==0.12.0 \
    trl==0.10.1 \
    bitsandbytes==0.43.3 \
    accelerate==0.33.0 \
    google-cloud-storage==2.18.0 \
    sentencepiece \
    protobuf

COPY train.py .

ENTRYPOINT ["python", "train.py"]
