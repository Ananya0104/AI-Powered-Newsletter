
# 📰 AI-Powered Newsletter Generator

An AI-powered personalized newsletter generator that fetches relevant news articles based on your profession and country using RSS feeds, extracts content, summarizes it using Hugging Face Transformers, and generates a Markdown newsletter.

---

## 🚀 Features

- Personalized news based on **Profession** and **Country**
- Pulls top stories from relevant **RSS Feeds**
- Uses Hugging Face Transformers for **text summarization** and **classification**
- Automatically generates a neatly formatted **Markdown newsletter**
- Simple **CLI interface** and **Streamlit web app** version available

---

## 📦 Installation

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/newsletter-generator.git
cd newsletter-generator
```

2. **Install the requirements**:

Make sure you have Python 3.7+ installed.

```bash
pip install -r requirements.txt
```

---

## 🧠 Setup Hugging Face API

Add your [Hugging Face API token](https://huggingface.co/settings/tokens) in the script:

```python
HF_TOKEN = "your_huggingface_api_token"
```

---

## 🖥️ Run the CLI Version

```bash
python main.py
```

You will be prompted with:

```
Enter details in format: Name(Profession, Age, Country):
> Ananya(Technology, 21, India)
```

This generates a Markdown file with relevant news summaries.

---

## 🌐 Run the Streamlit App

To run the interactive web app:

```bash
streamlit run app.py
```

Then open the provided `localhost` link in your browser.

---

## 📸 Streamlit App Screenshot

![Streamlit Screenshot](streamlit_app_screenshot.png)

> Replace this image with an actual screenshot of your app and save it as `screenshots/streamlit_ui.png`.

---

## 📁 Output Sample

The generated newsletter is saved as a Markdown file, e.g.:

```
Ananya_Newsletter.md
```

---

## 🗂️ Folder Structure

```
.
├── app.py
├── main.py
├── requirements.txt
├── README.md
├── streamlit_app_screenshot.png
```

---

