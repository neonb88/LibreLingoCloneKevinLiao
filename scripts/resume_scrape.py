#Pytesseract not found or Tesseract-OCR not installed. OCR functionality will be limited.
	#  NOTE:  Pytesseract does OCR.  PyPDF2 does not.               

'''					 

=================================================================================
	To-do:		run a resume through it and fix things.						 
		At this point, the code is purely generated through Gemini.						  
			(August 12, 2025)   

	Split skills by commas instead of just adding every word in.		(August 17, 2025)
		Skills was better right now compared to experience, etc.    
	It needs to get "experience" correctly.                      


=================================================================================
	(search for the shortest lines that contain the keywords for the headers)                       
		( ^   the earlier idea, in the line above            is better)   Search for lines with length 1, 2, or perhaps                           



	I can also try searching through the newlines                      






	If necessary, do NLP on the lines to detect which is "careers," "education," "skills," "," ","      etc.   .        
		(ie. use GlOVe for  common synonyms, etc.)                      


'''					 

import os
import re
from PyPDF2 import PdfReader
import pymupdf
from docx import Document
import spacy
from spacy.matcher import Matcher
import sys
import json

# --- Configuration ---
# Path to Tesseract executable (only if you're using pytesseract and it's not in your PATH)
# Example for Windows: TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
TESSERACT_PATH = None # Set this if Tesseract is not in your system's PATH

if TESSERACT_PATH:
	import pytesseract
	pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
else:
	try:
		import pytesseract
	except ImportError:
		print("Pytesseract not found or Tesseract-OCR not installed. OCR functionality will be limited.")
		pytesseract = None # Disable pytesseract if not available

# Load SpaCy model
try:
	nlp = spacy.load("en_core_web_sm")
except OSError:
	print("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
	nlp = None

# --- Helper Functions for Text Extraction ---

def extract_text_from_pdf(pdf_path):
	"""
	Extracts text from a digital PDF file.
	Note: This will not work for scanned PDFs (images).
	"""
	text = ""
	doc = pymupdf.open(pdf_path)
	TEXT_IDX = 4
	for i in range(doc.page_count):
		page = doc.load_page(i)
		print(page.get_text("blocks"))
		for block in page.get_text("blocks"):
			text += block[TEXT_IDX] + '\n'    #page.get_text("blocks")[TEXT_IDX] + '\n'
	return text, doc

def extract_text_from_docx(docx_path):
	"""
	Extracts text from a .docx file.
	"""
	text = ""
	try:
		document = Document(docx_path)
		for paragraph in document.paragraphs:
			text += paragraph.text + "\n"
	except Exception as e:
		print(f"Error extracting text from DOCX {docx_path}: {e}")
	return text

def extract_text_from_txt(txt_path):
	"""
	Extracts text from a .txt file.
	"""
	text = ""
	try:
		with open(txt_path, 'r', encoding='utf-8') as file:
			text = file.read()
	except Exception as e:
		print(f"Error extracting text from TXT {txt_path}: {e}")
	return text

def extract_text_from_image_or_scanned_pdf(file_path):
	"""
	Extracts text from an image or scanned PDF using Tesseract OCR.
	Requires Tesseract-OCR to be installed and pytesseract to be configured.
	For PDFs, you might need to convert PDF pages to images first (e.g., using Pillow or Poppler).
	This is a simplified example.
	"""
	if not pytesseract:
		print("Pytesseract is not available. Cannot perform OCR.")
		return ""

	try:
		# If it's a PDF, we assume it's a scanned PDF for OCR.
		# For better handling, you'd typically convert PDF pages to images first.
		# This example directly uses image_to_string, which might work for single-page PDFs
		# or require additional libraries like `Pillow` for multi-page TIFFs from PDFs.
		from PIL import Image # Pillow is used by pytesseract for image handling
		
		if file_path.lower().endswith('.pdf'):
			# For scanned PDFs, a more robust solution involves converting PDF to images
			# and then running OCR on each image. Poppler can help with this.
			# For simplicity, we'll try a direct approach which might not always work for multi-page PDFs
			# without prior image conversion.
			print(f"Attempting OCR on PDF: {file_path}. For multi-page scanned PDFs, consider converting to images first.")
			# A more robust solution would be:
			# from pdf2image import convert_from_path
			# images = convert_from_path(file_path)
			# text = ""
			# for img in images:
			#	  text += pytesseract.image_to_string(img)
			# return text
			# For now, let's just attempt a direct read which might fail for complex PDFs.
			return pytesseract.image_to_string(file_path) # pytesseract can sometimes directly process PDFs (needs Ghostscript)
		else: # Assume it's an image file (PNG, JPG, etc.)
			return pytesseract.image_to_string(Image.open(file_path))
	except Exception as e:
		print(f"Error performing OCR on {file_path}: {e}")
		return ""

# --- Resume Parsing Logic ---

# --- Configuration (Keep as is) ---
# ... (rest of the initial configuration and helper functions for text extraction) ...
try:
	nlp = spacy.load("en_core_web_sm")
except OSError:
	print("SpaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
	nlp = None

'''

The prompt I used to generate this code with Gemini (an LLM like ChatGPT) :                  







Hey Gemini,



Can you improve this resume scraping code to work for my resumes? The formats of the resumes will vary, but most will look similar to what I am giving you with these resumes. The keywords associated with each section are the important part; we need the resume parsing code to tell which section is "skills," "education," "occupational experience," "projects", etc. but also to be able to handle common synonyms for those words that appear in many resumes you can find on the internet, including ""education", "school", "university", "college", "degree", "bachelor", "master", "phd", "associate", etc." for educational keywords.



We need all the fields from their resume in different sections parsed out and stored in a separate nested python dictionary structure, like "{"customer_name": "Kevin", "experience": [('experience_0', ('Capital One', 'Full Stack Software Engineer', {'Position_start_and_end:', ('October 31, 2019', 'September 1, 2025')}, {'Skills associated with this job':, ('Python', 'ReactJS', 'SQL', 'Splunk', 'Jira', 'Java', )))... [('experience_1', ('Deloitte'), ... ] ]






'''

# --- Resume Parsing Logic (IMPROVED) ---

class ResumeParser:
	def __init__(self):
		self.nlp = nlp
		# Define keywords for section headers
		self.section_keywords = {
			'experience': ['occupational experience', 'experience', 'employment history', 'work history', 'professional experience', 'work'],
			'education': ['education', 'school', 'university', 'college', 'degree', 'academic background', 'academic qualifications'],
			'skills': ['skills', 'technical skills', 'proficiencies', 'technologies', 'programming'],
			'projects': ['projects', 'portfolio', 'personal projects'],
			'summary': ['summary', 'profile', 'objective', 'professional summary']
		}

	def _find_sections(self, text, pymu_doc):
		"""
		Identifies sections in the resume text based on keywords.
		Returns a dictionary where keys are section names (e.g., 'education')
		and values are the text content of those sections.
		"""
		sections = {}
		lines = text.split('\n')
		current_section = None
		
		# Create a regex pattern for all keywords to identify section headers
		all_keywords = [item for sublist in self.section_keywords.values() for item in sublist]
		# Match lines that consist solely of a keyword, case-insensitive
		header_pattern = re.compile(r"^\s*(" + "|".join(all_keywords) + r")\s*$", re.IGNORECASE)

		#  TODO: parse the pymu_doc and  into sections here .               
		"""
		# TODO: embeddings after getting the hard-coded regexes version working        
		from llama_index.embeddings import HuggingFaceEmbedding
		embed_model = HuggingFaceEmbedding(model_name="meta-llama/Llama-2-7b-chat-hf")
		embeddings = embed_model.get_text_embedding("Hello World!")
		"""

		def get_section_key(header_text):
			header_text = header_text.lower().strip()
			for key, keywords in self.section_keywords.items():
				if header_text in keywords:
					return key
			return None

		for line in lines:
			match = header_pattern.match(line)
			if match:
				section_key = get_section_key(match.group(1))
				if section_key:
					current_section = section_key
					sections[current_section] = []
					continue # Skip the header line itself

			if current_section and line.strip():
				if current_section in sections:
					sections[current_section].append(line)
				else:
					sections[current_section] = [line]
		
		# Join the lines back into a single string for each section
		for section_name, content_lines in sections.items():
			sections[section_name] = "\n".join(content_lines)
			
		# Handle cases where sections are not explicitly titled (e.g., contact info)
		# A more advanced implementation could use positional cues.
		return sections

	def parse_resume(self, file_path):
		"""
		Main function to parse a resume file. It extracts text, finds sections,
		parses each section, and formats the output.
		"""
		file_extension = os.path.splitext(file_path)[1].lower()
		raw_text = ""

		# --- (Keep your existing text extraction logic here) ---
		# For demonstration, I'll use a simplified call to a generic extractor
		raw_text, doc = self._universal_text_extractor(file_path)
		print("Raw text of the resume: ", raw_text)                        

		if not raw_text:
			return {"error": "Could not extract text from the resume."}

		# Find the sections within the resume
		sections = self._find_sections(raw_text, doc)

		# Extract information from each section
		contact_info = self._extract_contact_info(raw_text) # Contact info is usually at the top
		experience = self._extract_experience(sections.get('experience', ''))
		education = self._extract_education(sections.get('education', ''))
		skills = self._extract_skills(sections.get('skills', ''))

		# --- Assemble into the desired nested dictionary structure ---
		parsed_data = {
			"customer_name": contact_info.get("name", "N/A"),
			"experience": [],
			"education": education, # Assuming education format is a list of dicts
			"skills": skills, # Assuming skills format is a list or dict
			# Add other parsed sections as needed
		}

		# Format experience into the specific tuple structure requested
		for i, job in enumerate(experience):
			exp_tuple = (
				f'experience_{i}', (
					job.get('company', ''),
					job.get('title', ''),
					{'Position_start_and_end': (job.get('start_date', ''), job.get('end_date', ''))},
					{'Skills associated with this job': tuple(job.get('job_skills', []))}
					# Note: The original request format for skills was complex. A tuple is used here.
				)
			)
			parsed_data["experience"].append(exp_tuple)

		return parsed_data
		
	def _universal_text_extractor(self, file_path):
		# This is a stand-in for your multiple extract_text_from_* functions
		if file_path.lower().endswith('.pdf'):
			return extract_text_from_pdf(file_path)
		# Add other file types as in your original code
		return ""


	def _extract_contact_info(self, text):
		"""Extracts name, email, and phone from the top of the resume."""
		contact_info = {
			"name": "Not Found",
			"email": "Not Found",
			"phone": "Not Found"
		}
		
		# Name is usually the first line(s)
		lines = text.split('\n')
		if lines:
			# A simple heuristic: the first non-email/phone line with 2-3 words is the name.
			for line in lines[:3]:
				if '@' not in line and not re.search(r'\d', line):
					if 1 < len(line.split()) < 4:
						contact_info['name'] = line.strip()
						break
		
		# Email
		email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
		if email_match:
			contact_info["email"] = email_match.group(0)

		# Phone
		phone_match = re.search(r"(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}", text)
		if phone_match:
			contact_info["phone"] = phone_match.group(0)
			
		return contact_info

	def _extract_education(self, education_text):
		"""
		Parses the education section text.
		Handles multiple entries and various formats.
		"""
		if not education_text:
			return []

		education_entries = []
		# Entries are typically separated by blank lines or start with a university name.
		# We can split by lines and process them sequentially.
		
		lines = education_text.strip().split('\n')
		entry = {}
		for line in lines:
			line = line.strip()
			if not line:
				continue

			# Heuristic: If a line contains a university name or a date range,
			# and we already have an entry, save it and start a new one.
			# A simpler way is to assume each institution starts a new entry.
			is_new_entry = any(keyword in line for keyword in ['University', 'College', 'Institute']) or re.search(r'\d{4}', line)
			
			if is_new_entry and 'institution' in entry:
				education_entries.append(entry)
				entry = {}

			# Date patterns
			date_match = re.search(r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|January|February|March|April|May|June|July|August|September|October|November|December|Present|Current)\s+\d{4}|(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\s+-\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}|\b(20\d{2})\b', line, re.IGNORECASE)
			
			if date_match:
				entry['dates'] = date_match.group(0).strip()
			else:
				# Assume the rest is institution and degree info
				parts = [p.strip() for p in line.split('-') if p.strip()]
				if 'institution' not in entry and len(parts) > 0:
					entry['institution'] = parts[0]
					if len(parts) > 1:
						entry['degree'] = parts[1]
				elif 'degree' not in entry:
					entry['degree'] = line
		
		if entry: # Add the last processed entry
			education_entries.append(entry)
			
		return education_entries

	def _extract_experience(self, experience_text):
		"""
		Parses the occupational experience section.
		"""
		if not experience_text:
			return []
			
		experience_entries = []
		
		# A job entry seems to start with a line containing ' - ' (Title - Company)
		# We can split the text block by this pattern using a lookahead.
		job_blocks = re.split(r'\n(?=.*\s-\s.*\s-\s)', experience_text.strip())
		
		for block in job_blocks:
			if not block.strip():
				continue
				
			lines = block.strip().split('\n')
			entry = {'achievements': [], 'job_skills': []}

			# First line usually has Title, Company, Location
			header_match = re.match(r'^(.*)\s-\s(.*)\s-\s(.*)$', lines[0].strip())
			if header_match:
				entry['title'] = header_match.group(1).strip()
				entry['company'] = header_match.group(2).strip()
				entry['location'] = header_match.group(3).strip()

			# Second line often has dates
			if len(lines) > 1:
				date_match = re.search(r'(.*(?:19|20)\d{2})\s*-\s*(.*)', lines[1].strip(), re.IGNORECASE)
				if date_match:
					entry['start_date'] = date_match.group(1).strip().replace('Oct.', 'October')
					entry['end_date'] = date_match.group(2).strip()
				else: # if no date, assume it's part of description
					entry['achievements'].append(lines[1].strip())
			
			# Process remaining lines for achievements and skills
			is_in_skills_subsection = False
			for line in lines[2:]:
				line = line.strip()
				if line.lower().startswith('skills:'):
					is_in_skills_subsection = True
					line = line[len('skills:'):].strip() # Process remainder of the line

				if is_in_skills_subsection:
					skills = [s.strip() for s in line.split(',') if s.strip()]
					entry['job_skills'].extend(skills)
				else:
					# Remove bullet points for cleaner achievement text
					clean_line = re.sub(r'^\s*•\s*', '', line)
					if clean_line:
						entry['achievements'].append(clean_line)

			if 'title' in entry: # Only add valid entries
				experience_entries.append(entry)

		return experience_entries

	def _extract_skills(self, skills_text):
		"""
		Parses the skills section, looking for categories and lists of skills.
		"""
		if not skills_text:
			return {}

		skills_by_category = {}
		lines = skills_text.strip().split('\n')
		current_category = "General"
		
		for line in lines:
			# Check if the line is a sub-heading (e.g., a category)
			# Heuristic: it's short, doesn't contain common skill delimiters like ',',
			# and is followed by indented or listed items. This is complex,
			# so we'll use a simpler heuristic: if a line has no comma, it's a category.
			if ',' not in line and ':' not in line and len(line.split()) < 4:
				current_category = line.strip()
				skills_by_category[current_category] = []
			else:
				# Assumes skills are comma or newline separated
				skills = [s.strip() for s in re.split(r'[,•]', line) if s.strip()]
				if current_category not in skills_by_category:
					skills_by_category[current_category] = []
				skills_by_category[current_category].extend(skills)
		
		return skills_by_category

# --- Main Execution for Testing ---
if __name__ == "__main__":
	# Ensure SpaCy model is available
	if not nlp:
		sys.exit("SpaCy model not loaded. Exiting.")

	parser = ResumeParser()

	# Get the file path from command-line arguments or use the default
	if len(sys.argv) >= 2:
		resume_path = sys.argv[1]
	else:
		# Default path for testing - PLEASE UPDATE THIS to the correct path on your system
		# resume_path = "/Users/heavenlybamboo/Downloads/Resume - August 1, 2025.pdf"
		resume_path = "Resume - August 1, 2025.pdf" # Assumes file is in the same directory

	if not os.path.exists(resume_path):
		print(f"Error: Resume file not found at '{resume_path}'")
		print("Please provide the correct path as a command-line argument or update the default path in the script.")
	else:
		print(f"--- Parsing Resume: {resume_path} ---")
		parsed_data = parser.parse_resume(resume_path)
		
		# Pretty-print the final nested dictionary
		print(json.dumps(parsed_data, indent=2))




























































































