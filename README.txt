Steps to generate Synthesised text images

1. Clone this repo https://github.com/oh-my-ocr/text_renderer

2. In image folder ---> put refernce images that we need to generate. I have put the refernce images as Sample data given - https://drive.google.com/drive/folders/1JaWchvJVNfTJX_ThZefl6dtgfHC99q2W?usp=sharing

3. Main folder for us to use this repo(step 1) is the example_data folder. In folder bg i.e what background the synthesised images need to have. We can include such images.

4. char folder contains eng.txt that includes set of all characters for synthetic images.

5. font folder contains various .ttf files, i have mainly used Airal, Calibri and Times New Roman. We can add more text styles for diversity. fontlist.txt file contains the name of the above fonts.

6. Output folder contains the final generated text images. 

7. text folder contains eng_text.txt file any random para's of english text using characters in /char/eng.txt to generate synthetic data.

From text_renderer-master folder, execute the command- 

python3 main.py --config example_data/example.py --dataset img --num_processes 2 --log_period 10

Additional Configrations.

The main config file for synthetic text generation is example/example.py. 

Main Config Parameters in example.py are:

1. font_size
2. num_image for rand_data ---> No.of text images that has random characters in it from {a...z,A..Z,0-9,@,} present in /char/eng.txt. 
3. num_image for eng_word_data ---> No.of text images that has english meaningful phrase sampled randomly from \example_data\text. 
