import pandas as pd
import numpy as np
import glob
import sys


PATH_TO_TEST_ANNOTATION_FILE = 'C:\\Users\\user\\Desktop\\test_data\\public_test_annotations_final.csv'
PATH_TO_TXT_DUM_FILE = 'annotations-testing.txt'

PATH_TO_TEST_IMGS = PATH_TO_TEST_ANNOTATION_FILE.split('\\')[:-1]
PATH_TO_TEST_IMGS = "\\".join(PATH_TO_TEST_IMGS)
PATH_TO_TEST_IMGS = PATH_TO_TEST_IMGS + '\\public_test_crops\\'

dataframe = pd.read_csv(PATH_TO_TEST_ANNOTATION_FILE, index_col=0)

output_col1 = PATH_TO_TEST_IMGS + dataframe['Filename']
output_col2 = dataframe['Text']

#labels_test_np = output_col2.to_numpy()

#print(max(labels_test_np, key=len))
#print(len(max(labels_test_np, key=len)))

output_df = pd.concat([output_col1, output_col2], axis=1)
print(output_df)


output_df.to_csv(PATH_TO_TXT_DUM_FILE, index=False, header=False, sep=' ')
