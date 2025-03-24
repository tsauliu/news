
# Install Google Chrome
sudo apt update
sudo apt install -y google-chrome-stable
google-chrome --version

# Install ChromeDriver
wget https://storage.googleapis.com/chrome-for-testing-public/134.0.6998.165/linux64/chromedriver-linux64.zip # replace with the latest version
unzip  chromedriver-linux64.zip

# Install Python dependencies
pip install selenium