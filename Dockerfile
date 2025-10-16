# Dockerfile — Python 3.11 slim image (non-root user, /app chown'ed)
FROM python:3.11-slim

# Create /app and set it as working directory
WORKDIR /app

# Copy application files into container (only what we need)
COPY app.py /app/app.py

# Install runtime deps
RUN pip install --no-cache-dir flask

# Create dedicated group/user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Ensure /app is owned by appuser so the app can write there
RUN chown -R appuser:appgroup /app

# Expose the port the app listens on
EXPOSE 5000

# Switch to non-root user
USER appuser

# Start the Flask app
CMD ["python", "/app/app.py"]
