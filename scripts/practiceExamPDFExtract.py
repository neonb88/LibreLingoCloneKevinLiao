# src:   https://stackoverflow.com/questions/34837707/how-to-extract-text-from-a-pdf-file-via-python#comment104021550_48673754                  
import pymupdf # install using: pip install PyMuPDF

#fname_1 = "2023 May US SAT QAS recreation.pdf"    Much of this test isn't already converted to text   
fname_only_answers_are_already_searchable = "2023 March US SAT formatted with answers.pdf"
fname_1 = "2022 October US SAT QAS with answers and scoring - McElroy Tutoring.pdf"
with pymupdf.open(fname_1) as doc:
    text = ""
    for page in doc:
        text += page.get_text()

'''
	Sections of a test:
		1.  Reading passages:    demarcated by "following passage" and then numbers. 
		2.  Questions
		3.  Multiple choice answers
		4.

		But how do we automatically recognize these different sections?  Are the headers always the same?                      

'''

mode = "do not display"
"""
Modes:
	0.  "Do not display"
	1.  Part of the Reading Passage, or other reference information to display (Math, etc.)                  
	2.  Part of the question
	3.  Part of the multiple choice answers
	~~ 4.  Other reference information to display (Math, etc.) ~~                     I put this in the "just display this information" part of the app instead.    - June 28, 2025.  If this changes, I implore that you please document it appropriately.           


"""





curr_question_number = 0
curr_text_to_display = "Passage 1: "
curr_question_text = ""

for line in text:
	if mode == "Part of the Reading Passage, or other reference information to display":
		curr_text_to_display += line
	if "following passage" in line.lower():
		mode = "Part of the Reading Passage, or other reference information to display"

	num_digits = len(str(curr_question_number))
	if int( line[:num_digits] )  == curr_question_number + 1:
		probably_next_question = line[num_digits] in (" ", "\n") if len(line) > num_digits else True
		if probably_next_question:
			mode = "Part of the question"

print(text)

































































































