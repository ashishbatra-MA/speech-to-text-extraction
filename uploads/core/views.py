from django.shortcuts import render, redirect
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from google.cloud import speech
from uploads.core.models import Document
from uploads.core.forms import DocumentForm
import os
import io
import json
import pandas as pd
import re
import nltk
#import fuzzy
import six
from nltk.corpus import stopwords
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
#stop = stopwords.words('english')



os.environ['GOOGLE_APPLICATION_CREDENTIALS']='C:/Users/user/Documents/GitHub/speech-to-text-extraction/growth-solutions-6ef05c584635.json'




def simple_upload(request):
    if request.method == 'POST' and request.FILES['myfile']:
        myfile = request.FILES['myfile']
        fs = FileSystemStorage()
        filename = fs.save(myfile.name, myfile)
        uploaded_file_url = fs.url(filename)
        #data={}
        name = request.POST.get('name')
        application = request.POST.get('application')
        ppt = request.POST.get('ppt')
        preamnt = request.POST.get('preamnt')
        policy = request.POST.get('policy')
        product = request.POST.get('product')
        result = request.POST.get('result')
        print(name, application, ppt, preamnt, policy, product, result)
        data={"/media/audio_skxRzr2.wav": "Richa Goswami application number 30062 13998 exit exit that I have 10 and 30 1300 for 12 years for Tata AIA Life Is Life Insurance selling class I am buying 25 years I have confirmed and exothermic process for the"}
        #print('uploaded file url',filename)
        #transcript = transcribe_file_with_enhanced_model('media/'+filename)
        #data[uploaded_file_url] = transcript
        with open('output.json', 'w') as outfile:
            json.dump(data, outfile)
        print("dump in json")

        df = process_transcribed_text(data)

        extracted_personName = df.loc[0, "Person Name"]
        inputPersonName = "Richaa Gosswami"

        print(extracted_personName)
        print(inputPersonName)
        print("done")


        return render(request, 'core/home.html',)
    return render(request, 'core/simple_upload.html')


def model_form_upload(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = DocumentForm()
    return render(request, 'core/model_form_upload.html', {
        'form': form
    })

def transcribe_file_with_enhanced_model(path):
    print('transcribing file=',path)
    """Transcribe the given audio file using an enhanced model."""
    # [START speech_transcribe_enhanced_model]
    client = speech.SpeechClient()
    
    phrases =["application number","pay","rupees","buying","years","annually","TATA AIA Life Insurance","Sampoorna Raksha Plus","insurance","policy","monthly","premium"]
    print('Reading file now')
    
    # path = 'resources/commercial_mono.wav'
    with io.open(path, 'rb') as audio_file:
        content = audio_file.read()

    audio = speech.types.RecognitionAudio(content=content)
    config = speech.types.RecognitionConfig(
        encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=8000,
        language_code='en-IN',
        # Enhanced models are only available to projects that
        # opt in for audio data collection.
        use_enhanced=True,
        enable_automatic_punctuation=True,
        speech_contexts= [speech.types.SpeechContext(phrases = phrases)],
                # A model must be specified to use enhanced model.
#         model='phone_call')
        model='default')
#         model='command_and_search')
    print('calling speech api')
    response = client.recognize(config, audio)
#     response = client.long_running_recognize(config, audio)
    
    transcript_data=''
    for i, result in enumerate(response.results):
        alternative = result.alternatives[0]
#         print('result=',result)
        print('-' * 20)
#         print('First alternative of result {}'.format(i))
        print('Transcript: {}'.format(alternative.transcript))
        transcript_data = alternative.transcript
#         print('Transcript_data',transcript_data)
        break
    return transcript_data
    # [END speech_transcribe_enhanced_model]


def extract_person_name(text):
    """Detects entities in the text."""
    client = language.LanguageServiceClient()

    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')

    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects entities in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    entities = client.analyze_entities(document).entities

    # entity types from enums.Entity.Type
    entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')

    person_name = ''
    for entity in entities:
        # Only Person Type
        if entity.type == 1:
            person_name = entity.name
            break

    return person_name


def extract_application_number(document):
    lowercase_doc = document.lower()
    application_number=''
    if "application number" in document:
        application_index = document.index('application number')
        start_point = application_index + len('application number')
        endIndex = len(document)
        for i in range(start_point,len(document)):
    #         print(i, document[i])
            if not lowercase_doc[i].isdigit() and not lowercase_doc[i] == " " and not lowercase_doc[i] =='c':
                endIndex= i
                break
        application_number_withsapces =document[start_point:endIndex]
        application_number = application_number_withsapces.replace(" ","")
    return application_number


def extract_terms(document):
    lowercase_doc = document.lower()
    if "years" in document:
        premium_term_index = document.index('years')
        end_Index = premium_term_index - 1
        #     print(end_Index, 'Document value',document[end_Index+1])
        for i in range(end_Index, 0, -1):
            #         print(i, document[i])
            if not document[i].isdigit() and not document[i] == " ":
                start_point = i + 1
                break
        premium_term_withsapces = document[start_point:end_Index]
        #     print('Premium Term',premium_term_withsapces)
        premium_term = premium_term_withsapces.replace(" ", "")

        # policy terms
    #
    else:
        premium_term = ""
        premium_term_index = 0

    return premium_term, premium_term_index



def extract_product(document):
    tata_product = ('Smart Income Plus', 'Sampoorna Raksha Plus', 'Sampoorna Raksha')
    lowercase_doc = document.lower()
    product_name =''
    for each_product in tata_product:
        product_lower = each_product.lower()
#         print('searching product',product_lower)
        if product_lower in lowercase_doc:
            product_name = each_product
            break
    return product_name


def extract_premium_amount(document):
    amount_connotation = ('pay rupees', 'pay rs')
    lowercase_doc = document.lower()
    buffer_length =len(amount_connotation[0]);
#     print('connotation',amount_connotation[0])
    amount =''
    if amount_connotation[0] in lowercase_doc or amount_connotation[1] in lowercase_doc:
        if amount_connotation[0] in lowercase_doc:
            amount_start_index = lowercase_doc.index(amount_connotation[0])
        else:
            amount_start_index = lowercase_doc.index(amount_connotation[1])
            buffer_length =len(amount_connotation[1])
        start_point = amount_start_index + buffer_length
        for i in range(start_point,len(document)):
    #         print(i, document[i])
            if not lowercase_doc[i].isdigit() and not lowercase_doc[i] == " ":
                endIndex= i
                break
        amount_withsapces =lowercase_doc[start_point:endIndex]
        amount = amount_withsapces.replace(" ","")
    return amount


def process_transcribed_text(transcribe_dict):
    df = pd.DataFrame(columns=['Audio', 'Transcribed Text', 'Person Name', 'Application Number', 'Premium Payment Term',
                               'Premium Amount',
                               'Policy Term', 'Product', 'Result for Text Extraction'])
    row = 0
    for key, value in transcribe_dict.items():
        print('=' * 20)
        print('Processing Audio File', key)
        string = value
        person_name = extract_person_name(string)
        application_number = extract_application_number(string)
        policy_term, policy_term_index = extract_terms(string)
        second_part_doc_start_index = policy_term_index + len('years')
        premium_term, premium_term_index = extract_terms(string[second_part_doc_start_index:])
        product_name = extract_product(string)
        premium_amount = extract_premium_amount(string)

        df.loc[row, 'Audio'] = key
        df.loc[row, 'Transcribed Text'] = value
        df.loc[row, 'Person Name'] = person_name
        df.loc[row, 'Application Number'] = application_number
        df.loc[row, 'Premium Payment Term'] = premium_term
        df.loc[row, 'Premium Amount'] = premium_amount
        df.loc[row, 'Policy Term'] = policy_term
        df.loc[row, 'Product'] = product_name
        result = ''

        if not person_name.strip():
            result += "Person Name Error /"
        if not application_number.strip():
            result += "Application Number Error /"
        if not premium_term.strip():
            result += "Premium Term Error /"
        if not premium_amount.strip():
            result += "Premium Amount Error /"
        if not policy_term.strip():
            result += "Policy Term Error /"
        if not product_name.strip():
            result += "Product Name Error /"
        if result == '':
            result += "Pass"

        df.loc[row, 'Result'] = result

        row += 1

        print('Audio File:', key)
        print('Name of Person:', person_name)
        print('Application Number:', application_number)
        print('Premium Payment Term:', premium_term, 'years')
        print('Premium Amount:', premium_amount)
        print('Policy Term:', policy_term, 'years')
        print('Product:', product_name)
        print('Result:', result)
    return df;
