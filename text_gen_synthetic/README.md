Steps to generate Synthesized text images

1. Clone this repo https://github.com/oh-my-ocr/text_renderer

2. In image folder ---> put refernce images that we need to generate. I have put the refernce images as Sample data given - https://drive.google.com/drive/folders/1JaWchvJVNfTJX_ThZefl6dtgfHC99q2W?usp=sharing

3. example_data folder ---> Main folder for us to use this repo(step 1). In folder example_data/bg i.e what background the synthesized images need to have. We can include such images.

4. char folder contains eng.txt that includes set of all characters for synthetic images.

5.example_data/font folder contains various .ttf files, I have mainly used Airal, Calibri and Times New Roman font files. We can add more text styles for diversity. 
example_data/fontlist.txt file contains the list of the name of the above fonts.

6. example_data/output folder contains the final generated text images along with the corrosponding annotations in a JSON file.

7. example_data/text folder contains eng_text.txt file - any random para's of english text using characters in example_data/char/eng.txt to generate synthetic data.

From text_renderer-master folder, execute the command- 

python main.py --config example_data/example.py --dataset img --num_processes 2 --log_period 10

Additional Configrations.

The main config file for synthetic text generation is example/example.py. 

Main Config Parameters in example.py are:

1. font_size
2. num_image for rand_data ---> No. of text images that has random characters in it from {a...z,A..Z,0-9} present in /char/eng.txt. 
3. num_image for eng_word_data ---> No.of text images that has english meaningful phrase sampled randomly from example_data/text. 
