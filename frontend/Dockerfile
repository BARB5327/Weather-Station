FROM python:3.9

WORKDIR /frontend

COPY requirements.txt ./requirements.txt

RUN pip3 install -r requirements.txt

COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8080

# Set the environment variable PORT
ENV PORT 8080

# Start the Streamlit app
CMD ["streamlit", "run", "--server.port", "8080", "dashboard.py"]
