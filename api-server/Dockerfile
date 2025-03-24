FROM --platform=linux/amd64 python:3.12

WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt /app

RUN apt-get update

RUN apt-get install -y xvfb

# Disable interactive prompts during build
ENV DEBIAN_FRONTEND=noninteractive

# Download the Chrome .deb package.
RUN wget -O /tmp/google-chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"

# Install the package, fix missing dependencies, and clean up.
RUN dpkg -i /tmp/google-chrome.deb || apt-get install -y -f && \
  rm /tmp/google-chrome.deb && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

# Install the dependencies
# --no-cache-dir is used to avoid caching the package index and installed packages to reduce the image size
# --upgrade is used to ensure that the latest versions of the packages are installed (respecting constraints in requirements.txt)
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the source code directory into the container
# I know, having an app folder inside an app folder is weird but this was a quick fix lol
COPY app /app/app

# Expose application port
EXPOSE 80

# Run the FastAPI application using uvicorn
CMD ["sh", "-c", "alembic upgrade head && xvfb-run uvicorn app.main:app --host 0.0.0.0 --port 80 ${DEV:+--reload}"]