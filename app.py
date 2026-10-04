from flask import Flask, render_template_string, request
from pypdf import PdfReader
from docx import Document
import os
import re

app = Flask(__name__)

# Maximum upload size: 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {"pdf", "docx"}

SKILLS = [
    "python",
    "java",
    "c",
    "c++",
    "sql",
    "git",
    "flask",
    "django",
    "html",
    "css",
    "javascript",
    "react",
    "api testing",
    "data structures",
    "verilog",
    "vlsi",
    "digital electronics",
    "machine learning",
    "communication",
    "rtl",
    "cadence",
    "linux",
    "embedded systems",
    "microcontrollers",
    "matlab",
    "systemverilog",
    "asic",
    "fpga",
    "cmOS"
]


HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <title>SkillProof - Resume Analyzer</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f1f5ff;
            color: #172554;
            max-width: 900px;
            margin: 35px auto;
            padding: 20px;
        }

        h1 {
            color: #315fe8;
        }

        .card {
            background: white;
            padding: 25px;
            margin: 18px 0;
            border-radius: 15px;
            box-shadow: 0 4px 15px #dce4f5;
        }

        textarea {
            width: 100%;
            height: 130px;
            padding: 10px;
            box-sizing: border-box;
            border: 1px solid #ccd5e5;
            border-radius: 8px;
            margin: 8px 0 18px;
        }

        input[type="file"] {
            margin: 10px 0 18px;
            padding: 10px;
            width: 100%;
            border: 1px solid #ccd5e5;
            border-radius: 8px;
            box-sizing: border-box;
        }

        button {
            background: #315fe8;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }

        button:hover {
            background: #244bc2;
        }

        .score {
            font-size: 32px;
            font-weight: bold;
            color: #16845b;
        }

        .missing {
            color: #bd6418;
        }

        .matched {
            color: #16845b;
        }

        .file-info {
            background: #eef4ff;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .error {
            background: #ffe8e8;
            color: #a33;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }

        .divider {
            text-align: center;
            margin: 20px 0;
            color: #777;
        }

        small {
            color: #666;
        }
    </style>
</head>

<body>

    <h1>SkillProof</h1>
    <p>Smart Resume and Job Readiness Analyzer</p>

    <div class="card">

        <form method="POST" enctype="multipart/form-data">

            <label>
                <b>Upload your resume</b>
            </label>

            <input
                type="file"
                name="resume_file"
                accept=".pdf,.docx"
            >

            <small>
                Supported formats: PDF and DOCX. Maximum size: 5 MB.
            </small>

            <div class="divider">
                OR
            </div>

            <label>
                <b>Paste your resume text</b>
            </label>

            <textarea
                name="resume"
                placeholder="Example: I know Python, SQL and Git."
            >{{ resume }}</textarea>


            <label>
                <b>Paste the job description</b>
            </label>

            <textarea
                name="job"
                required
                placeholder="Example: Required skills: Python, SQL, Flask"
            >{{ job }}</textarea>

            <button type="submit">
                Analyze My Skills
            </button>

        </form>

    </div>


    {% if error %}

    <div class="card error">
        <b>Error:</b> {{ error }}
    </div>

    {% endif %}


    {% if uploaded_file %}

    <div class="card file-info">
        📄 Resume uploaded:
        <b>{{ uploaded_file }}</b>
    </div>

    {% endif %}


    {% if result %}

    <div class="card">

        <h2>Analysis Results</h2>

        <p class="score">
            {{ result.score }}% Match
        </p>


        <h3 class="matched">
            Matched Skills
        </h3>

        <p>
            {{ result.matched | join(', ') or 'No matching skills found' }}
        </p>


        <h3 class="missing">
            Missing Skills
        </h3>

        <p>
            {{ result.missing | join(', ') or 'No missing detected skills' }}
        </p>


        <h3>
            Recommended Next Step
        </h3>

        {% if result.missing %}

            <p>
                Start learning and practising:
                <b>{{ result.missing | join(', ') }}</b>.
            </p>

        {% else %}

            <p>
                Great! Practise technical questions
                and prepare to explain your projects.
            </p>

        {% endif %}


        <small>
            This score measures detected skills,
            not your chance of getting hired.
        </small>

    </div>

    {% endif %}

</body>
</html>
"""


def allowed_file(filename):
    """Check whether the uploaded file is PDF or DOCX."""

    if "." not in filename:
        return False

    extension = filename.rsplit(".", 1)[1].lower()

    return extension in ALLOWED_EXTENSIONS


def extract_pdf_text(file):
    """Extract text from a PDF file."""

    reader = PdfReader(file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_docx_text(file):
    """Extract text from a DOCX file."""

    document = Document(file)

    text = ""

    for paragraph in document.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_resume_text(file):
    """Read the uploaded resume and return its text."""

    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        return extract_pdf_text(file)

    if filename.endswith(".docx"):
        return extract_docx_text(file)

    return ""


def detect_skills(text):
    """Detect known skills from text."""

    text = text.lower()

    found = []

    for skill in SKILLS:

        skill_lower = skill.lower()

        # Special handling for C++
        if skill_lower == "c++":
            pattern = r"(?<!\w)c\+\+(?!\w)"

        # Special handling for C
        elif skill_lower == "c":
            pattern = r"(?<!\w)c(?!\w)"

        else:
            pattern = r"(?<!\w)" + re.escape(skill_lower) + r"(?!\w)"

        if re.search(pattern, text):
            found.append(skill)

    return sorted(set(found))


@app.route("/", methods=["GET", "POST"])
def home():

    resume = ""
    job = ""
    result = None
    error = None
    uploaded_file = None

    if request.method == "POST":

        resume = request.form.get("resume", "")
        job = request.form.get("job", "")

        uploaded = request.files.get("resume_file")

        # --------------------------------
        # STEP 1: Read uploaded resume
        # --------------------------------

        if uploaded and uploaded.filename:

            uploaded_file = uploaded.filename

            if not allowed_file(uploaded.filename):

                error = "Please upload only a PDF or DOCX file."

            else:

                try:

                    extracted_text = extract_resume_text(uploaded)

                    if extracted_text.strip():

                        resume = extracted_text

                    else:

                        error = (
                            "Could not extract text from this resume. "
                            "If it is a scanned/image-only PDF, "
                            "please use the paste-text option for now."
                        )

                except Exception as e:

                    error = "Could not read the uploaded resume."


        # --------------------------------
        # STEP 2: Analyze skills
        # --------------------------------

        if not error and resume and job:

            resume_skills = detect_skills(resume)

            job_skills = detect_skills(job)

            matched = sorted(
                set(resume_skills) & set(job_skills)
            )

            missing = sorted(
                set(job_skills) - set(resume_skills)
            )

            score = (
                round(len(matched) / len(job_skills) * 100)
                if job_skills
                else 0
            )

            result = {
                "matched": matched,
                "missing": missing,
                "score": score
            }


        elif not error and not resume:

            error = "Please upload a resume or paste your resume text."


        elif not error and not job:

            error = "Please enter the job description."


    return render_template_string(
        HTML,
        resume=resume,
        job=job,
        result=result,
        error=error,
        uploaded_file=uploaded_file
    )


if __name__ == "__main__":
    app.run(debug=True)  