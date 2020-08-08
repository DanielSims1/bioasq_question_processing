# bioasq_question_processing

1. Download pre-train model for question type classification:

https://drive.google.com/drive/u/1/folders/1iv7ZXuLAPZGFGsxlgIm2Zi8NBEsvvliq

2. Change path in line:

jsonFile = open('/content/gdrive/My Drive/Colab Notebooks/BioASQ/training8b.json', 'r')

test_data_path = '/content/gdrive/My Drive/Colab Notebooks/BioASQ/input.csv'

model = BertForSequenceClassification.from_pretrained('/content/gdrive/My Drive/Colab Notebooks/BioASQ/Model/model 1/', cache_dir=None)

tree.write('gdrive/My Drive/Colab Notebooks/BioASQ/qp_demo.xml', pretty_print=True)

3. Run:
Run python code in Demo_Question_Processing.ipynb, it will use 'input.csv' as input, and give output 'qp_demo.xml' 
