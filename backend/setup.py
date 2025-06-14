from setuptools import setup, find_packages

setup(
    name="resumatch-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.95.1",
        "uvicorn==0.22.0",
        "python-multipart==0.0.6",
        "requests==2.29.0",
        "pyjwt==2.6.0",
        "pydantic==1.10.7",
        "pdfplumber==0.9.0",
        "PyMuPDF==1.22.3",
        "python-dotenv==1.0.0",
        "httpx==0.23.3",
        "supabase==1.0.3",
        "numpy==1.24.3",
        "scikit-learn==1.2.2",
        "transformers==4.29.2",
        "sentence-transformers==2.2.2",
        "llama-cpp-python==0.2.19",
    ],
    python_requires=">=3.11",
) 