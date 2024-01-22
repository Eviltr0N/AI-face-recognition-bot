import boto3
import io
from PIL import Image, ImageDraw, ImageFont, ImageColor
import matplotlib.pyplot as plt

rekognition = boto3.client('rekognition', region_name='us-east-1')
dynamodb = boto3.client('dynamodb', region_name='us-east-1')



font = ImageFont.truetype('DejaVuSans.ttf', 30)

# set up colors
colors = ['green', 'red', 'blue', 'yellow', 'purple', 'orange', 'pink', 'brown', 'cyan', 'magenta', 'gold', 'violet', 'navy', 'turquoise', 'lime', 'maroon', 'teal', 'olive', 'grey', 'black']
# iterate over face details



def get_face_details(image_path, is_celeb):

    if not is_celeb:
        img = Image.open(image_path)
        stream = io.BytesIO()
        img.save(stream,format="JPEG")
        image_binary = stream.getvalue()

        try:

            response = rekognition.search_faces_by_image(
                    CollectionId='minor_facerecognition',
                    Image={'Bytes':image_binary}
                    )
        except Exception as e:
            print('Excception Occured:', e)
            return []

        found = False
        for match in response['FaceMatches']:
            print (match['Face']['FaceId'],match['Face']['Confidence'])
            accuracy = match['Face']['Confidence']

            face = dynamodb.get_item(
                TableName='facerecognition',
                Key={'RekognitionId': {'S': match['Face']['FaceId']}}
                )

            if 'Item' in face:
                print ("Found Person: ",face['Item']['FullName']['S'])
                found = True
                first_face_name = face['Item']['FullName']['S']
        if not found:
            print("Person cannot be recognized")
            first_face_name = 'Person1'
            accuracy = 'Not available'
    #=================================

        response = rekognition.detect_faces(Image={'Bytes':image_binary}, Attributes=['ALL'])

        total_faces = len(response['FaceDetails'])

        print('Here is length',len(response['FaceDetails']))

        draw = ImageDraw.Draw(img)

        data_list = []

        for i, face_detail in enumerate(response['FaceDetails']):
            if i+1 == 1:
                name = first_face_name
            else:
                name = f'Person{i+1}'

            print('Name:', name)

            age_range = face_detail['AgeRange']
            print(f"Age Range: {age_range['Low']} - {age_range['High']}")

            # Get the smile value
            smile = face_detail['Smile']['Value']
            print(f"Smiling: {smile}")

            # Get the eyeglasses value
            eyeglasses = face_detail['Eyeglasses']['Value']
            print(f"Eyeglasses: {eyeglasses}")

            # Get the gender value
            gender = face_detail['Gender']['Value']
            print(f"Gender: {gender}")

            # If gender is male, get the beard and mustache values
            if gender == 'Male':
                beard = face_detail['Beard']['Value']
                mustache = face_detail['Mustache']['Value']
                print(f"Beard: {beard}")
                print(f"Mustache: {mustache}")

            # Get the emotion with the highest confidence
            emotions = face_detail['Emotions']
            max_confidence = 0
            max_emotion = ''
            for emotion in emotions:
                if emotion['Confidence'] > max_confidence:
                    max_confidence = emotion['Confidence']
                    max_emotion = emotion['Type']
            print(f"Emotion: {max_emotion}")
            print()

            if gender == 'Male':
                data_str = f"Name: {name} \nAge Range: {age_range['Low']} - {age_range['High']} \nSmiling: {smile} \nEyeglasses: {eyeglasses} \nGender: {gender} \nBeard: {beard} \nMustache: {mustache} \nEmotion: {max_emotion} \nAccuracy: {accuracy}"
            else:
                data_str = f"Name: {name} \nAge Range: {age_range['Low']} - {age_range['High']} \nSmiling: {smile} \nEyeglasses: {eyeglasses} \nGender: {gender} \nEmotion: {max_emotion} \nAccuracy: {accuracy}"

            data_list.append(data_str)

            # get bounding box coordinates
            bb = face_detail['BoundingBox']
            left = bb['Left'] * img.size[0]
            top = bb['Top'] * img.size[1]
            width = bb['Width'] * img.size[0]
            height = bb['Height'] * img.size[1]
            right = left + width
            bottom = top + height

            color = colors[i % len(colors)]
            rgb = ImageColor.getrgb(color)
            # draw the boundary box
            draw.rectangle([left, top, right, bottom], outline=rgb, width=5)

            # draw the person's name below the boundary box
            text_bbox = draw.textbbox((left, top + height), name, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            draw.text(((left+right)/2-text_width/2, bottom+10), name, font=font, fill=rgb)

        # save edited image
        img.save('edited.jpg')


        if total_faces > 1:
            data_list.insert(0, f'Total Persons Found: {total_faces}' )
            return data_list
        else:
            return data_list

# ****************************************************

# def get_celeb_details(image_path):

    else:
        img = Image.open(image_path)
        stream = io.BytesIO()
        img.save(stream, format="JPEG")
        image_binary = stream.getvalue()

        response = rekognition.recognize_celebrities(Image={'Bytes':image_binary})


        data_list = []

        for i, celeb in enumerate(response['CelebrityFaces']):
            name = celeb['Name']
            wiki_url = celeb['Urls'][0]
            data_list.append(f'Name: {name} \nMore Info: {wiki_url}')
            bb = celeb['Face']['BoundingBox']
            left = bb['Left'] * img.size[0]
            top = bb['Top'] * img.size[1]
            width = bb['Width'] * img.size[0]
            height = bb['Height'] * img.size[1]
            right = left + width
            bottom = top + height

            color = colors[i % len(colors)]
            rgb = ImageColor.getrgb(color)

            # draw the boundary box
            draw = ImageDraw.Draw(img)
            draw.rectangle([left, top, right, bottom], outline=rgb, width=5)

            # draw the person's name below the boundary box
            text_bbox = draw.textbbox((left, top + height), name)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            draw.text(((left+right)/2-text_width/2, bottom+10), name, fill=rgb)

        # save edited image
        img.save('edited.jpg')

        return data_list

# print('\n\n\n\n\n')

# image_path = input("Enter path of the image to check: ")
# print(get_face_details(image_path))
