FROM python:3.8
WORKDIR /backend
COPY . ./
RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python"]
CMD ["backend.py"]
