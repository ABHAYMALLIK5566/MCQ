# Spiritual MCQ Generator

A web application that generates Multiple Choice Questions (MCQs) from uploaded documents using Google's Generative AI (Gemini).

## Features

- **Document Upload**: Support for PDF, DOC, DOCX, PPT, PPTX, and TXT files
- **AI-Powered MCQ Generation**: Uses Google's Gemini AI to generate questions
- **Difficulty Levels**: Easy, Medium, and Hard difficulty options
- **Page Range Selection**: Specify which pages to extract text from
- **User Authentication**: Register and login with email/password
- **API Key Management**: Store and manage your Gemini API key

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Running the Application

1. **Clone the repository**:
   ```bash
   git clone https://github.com/ABHAYMALLIK5566/Quiz_MCQ.git
   cd Quiz_MCQ
   ```

2. **Start the application**:
   ```bash
   sudo docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

### Usage

1. **Register**: Create an account with your email, password, and Gemini API key
2. **Login**: Sign in with your credentials
3. **Upload Document**: Select a document file (PDF, DOC, DOCX, PPT, PPTX, TXT)
4. **Configure Settings**: Choose number of questions, difficulty level, and page range
5. **Generate MCQs**: Click "Generate MCQs" to create questions
6. **Download**: Download the generated MCQs as a text file

## Architecture

- **Frontend**: Streamlit web application
- **Backend**: FastAPI REST API with PostgreSQL database
- **AI**: Google Generative AI (Gemini) for MCQ generation
- **Containerization**: Docker and Docker Compose for easy deployment

## API Endpoints

- `POST /register` - User registration
- `POST /token` - User login
- `POST /generate` - Generate MCQs from uploaded file
- `GET /health` - Health check endpoint

## Development

To run in development mode:

```bash
# Build and start services
sudo docker-compose up -d

# View logs
sudo docker-compose logs -f

# Stop services
sudo docker-compose down
```

## Troubleshooting

- **Database Connection Issues**: The backend includes automatic retry logic for database connections
- **Permission Issues**: Make sure your user is in the docker group or use sudo
- **Port Conflicts**: Ensure ports 8000 and 8501 are available

## License

This project is open source and available under the MIT License.