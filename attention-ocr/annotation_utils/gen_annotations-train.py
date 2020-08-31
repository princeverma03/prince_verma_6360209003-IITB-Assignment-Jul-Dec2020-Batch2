import glob
import os
import json

PATH_TO_DATABASE = 'E:\\ocr_database\\*'
FILE_DUMP_NAME = '.\\annotations-'

def generate_annotation_textfile(corpuses_path):
    '''
    generate_annotation_textfile generates a text file containing text of format --
    <PATH_TO_IMAGES> <space> <LABEL> (of corrosponding image)

    Arguments:
    corpuses_path - List of absolute paths of directories.

    Returns:
    True if everything is success.
    '''
    print(corpuses_path)
    for corpus_path in corpuses_path:

        label_file_path = corpus_path + '\\labels.json'
        root_dir_filename = corpus_path.split('\\')[-1]
        filedump_name = FILE_DUMP_NAME + root_dir_filename + '.txt' 

        filedump = open(filedump_name, 'a')

        root_dir_path_list = PATH_TO_DATABASE.split('\\')[:-1]
        root_dir_path = '\\'.join(root_dir_path_list)
        absolute_image_path = root_dir_path + '\\' + root_dir_filename + '\\images\\'
    
        with open(label_file_path, 'r') as file:
        
            label_data_dict = json.load(file)
            num_samples = label_data_dict['num-samples']        
            labels_dict = label_data_dict['labels']

            image_size_dict = label_data_dict['sizes']
            print(max(image_size_dict.values()))            

            image_file_counter = 1
        
            for image_name, image_label in labels_dict.items():
            
                filedump_data = absolute_image_path + image_name + '.jpg' + ' ' + image_label

                if image_file_counter != num_samples:
                    filedump_data = filedump_data + '\n'

                filedump.write(filedump_data)
                image_file_counter += 1
            
            print('Dumping of a file completed, {} samples of images, please check!'.format(image_file_counter - 1))

        filedump.close()
    return True

if __name__ == '__main__':

    corpuses_path = glob.glob(PATH_TO_DATABASE)
    print('corpuses_path: ',corpuses_path)
    generate_annotation_textfile([corpuses_path[-3]])
    print('Dumping completed')
