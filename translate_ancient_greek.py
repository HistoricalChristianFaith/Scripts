import sys
import os
import argparse
import traceback
import time

# pip install --upgrade openai
import openai

def setup_bite_size_chunks(fname):

    f = open(fname, 'r')
    text = f.read()
    f.close()

    l = text.replace("\n", " ")
    l = l.strip()
    final_l = ""
    quotes_open = 0
    paren_open = 0
    sqparen_open = 0
    current_count = 0
    for c in l:
        if current_count == 0 and c == " ":
            current_count += 1
        else:
            if c == '"':
                if quotes_open:
                    quotes_open = 0
                else:
                    quotes_open = 1
            #if c == '(':
            #    paren_open = 1
            #if c == ')':
            #    paren_open = 0
            #if c == '[':
            #    sqparen_open = 1
            #if c == ']':
            #    sqparen_open = 0
            final_l += c
            current_count += 1
            if current_count > 400 and not quotes_open and not paren_open and not sqparen_open and c in [".", "?", "!"]:
                final_l += "\n"
                current_count = 0

    # Save this so we can review it, etc.
    f = open(fname+".bitesize", "w")
    f.write(final_l)
    f.close()
    print(fname+".bitesize created! You probably want to manually review/tweak it before proceeding. The Translation API doesn't work well for HUGE chunks of text.")


def translate(fname):

    f = open(fname+".bitesize", 'r')
    input_lines = f.readlines()
    f.close()

    full_translated_text = ""
    for x in input_lines:
        x = x.strip()
        print(x)
        skip = False
        if "<" and ">" in x:
            skip = True
        
        if len(x) < 20:
            skip = True

        if skip:
            # just pass untranslated payload into output:
            #full_translated_text += x + "\n"
            full_translated_text = x + "\n"
        else:
            # translate, then put translated text in output

            #########

            # Step 1: send the conversation and available functions to GPT

            try:
                y = request_chatgpt_translation(x)
            except Exception:
                print(traceback.format_exc())
                print("*****waiting 1 minute and trying again...")
                '''
                time.sleep(60)

                try:
                    y = request_chatgpt_translation(x)
                except Exception:
                    print(traceback.format_exc())
                    print("*****[Failed twice] waiting 5 minute and trying again...")
                    time.sleep(300)
                    y = request_chatgpt_translation(x)
                '''




            ###########

            print(y)
            print("*************")
            translated_text = parse_translation_json(y['choices'][0]['message']['function_call']['arguments'])
            
            """
            Still fails in the case of a quotation mark inside the json payload, which should be double-escaped (but is only single-escaped)

            E.g. "{\n  \"english_text\": \"The fourth (sign) is (that) of false prophets and false apostles, about whom the apostle says: 'Such pseudo-apostles, workers of iniquity, transform themselves into apostles of Christ, who say: \"Thus says the Lord\", and the Lord has not sent them' (2 Cor. X, 13). But such is not the apostle Paul, who was sent not by men, nor through man, but by God the Father through Jesus Christ. From this it is affirmed that the heresies of Ebion and Photinus must be refuted, because our Lord Jesus Christ is God, (which is evident) since the Apostle, who was sent by Christ to proclaim the Gospel, denies that he was sent by man.\"\n}"

            \"Thus says the Lord\" should be \\\"Thus says the Lord\\\"... I think
            """

            #full_translated_text += translated_text + "\n"
            full_translated_text = translated_text + "\n"
            time.sleep(3)

        textfile = open(fname+".translatedbitesize", "a")
        textfile.write(full_translated_text)
        textfile.close()



def request_chatgpt_translation(txt):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that translates Latin to English. Translate the user's message into English."},
        {"role": "user", "content": txt}
    ]

    functions = [
        {
            "name": "save_english_to_database",
            "description": "Saves an english translation of a latin text into a database. ",
            "parameters": {
                "type": "object",
                "properties": {
                    "english_text": {
                        "type": "string",
                        "description": "An English translation of a Latin text exactly as-is with no additional commentary.",
                    },
                },
                "required": ["english_text"],
            },
        }
    ]
    y = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        functions=functions,
        function_call={"name": "save_english_to_database"}, 
    )
    return y


def parse_translation_json(raw_json_translation):
    raw_json_translation = raw_json_translation.replace('"english_text":"', '"english_text": "')
    raw_json_translation = raw_json_translation.replace('"english_text" : "', '"english_text": "')

    raw_json_translation = raw_json_translation.split('"english_text": "')[1]
    raw_json_translation = raw_json_translation.replace("\n", "")

    if raw_json_translation[-4:] == '"  }':
        raw_json_translation = raw_json_translation.replace('"  }', '"}')
    if raw_json_translation[-3:] == '" }':
        raw_json_translation = raw_json_translation.replace('" }', '"}')
    if raw_json_translation[-3:] == '",}':
        raw_json_translation = raw_json_translation.replace('",}', '"}')
    if raw_json_translation[-3:] == '", }':
        raw_json_translation = raw_json_translation.replace('", }', '"}')
    if raw_json_translation[-3:] == '""}':
        raw_json_translation = raw_json_translation.replace('""}', '"}')
    if raw_json_translation[-1:] == '"':
        raw_json_translation += "}"

    raw_json_translation = raw_json_translation.split('"}')[0].strip()

    if raw_json_translation[-1:] == '}':
        raw_json_translation = raw_json_translation[:-1]

    return raw_json_translation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate a file of Ancient Greek into English')

    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Filename of Ancient Greek file."
    )

    parser.add_argument(
        "-a",
        "--apikey",
        type=str,
        help="OpenAI api key",
    )

    parser.add_argument(
        "-s",
        "--step",
        type=str,
        help="Step (bitesize, translate, all)",
        default="all"
    )

    args = parser.parse_args()

    fname = args.filename
    step = args.step
    openai.api_key = args.apikey

    print(fname)

    if step in ['bitesize', 'all']:
        print("setup_bite_size_chunks...")
        setup_bite_size_chunks(fname)

    if step in ['translate', 'all']:
        print("translate...")
        translate(fname)
