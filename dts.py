# print("iniciando")
import json, time, os, sys, unicodedata, re
# print("importando modulos de google")
import google.genai as genai
# print("resolviendo tipos")
import google.genai.chats as types
# print("configurando")
# Chats: list[genai.client.Chat] = []
# Chats: list[types.Chat] = []
SwitchIndex = 0


ApiKeys = [
    # lista de tonkens de gemini
]

route_input_file = 'lang_input.json'
route_strings_file = 'strings.json'

route_map_file = 'map_keys.json'
route_ja_input_file = 'lang_ja.json'


route_output_file = 'lang_es_out.json'
route_strings_result_file = 'strings_es.json'

route_manual_file = 'lang_manual_edit.json'
prompt = (
    "Actúa como un traductor profesional de nivel C2 de ingles el cual tu rol va a ser traducir diálogos de un juego respetando el orden de los diálogos y conservando la coherencia entre ellos"
    " vas a traducir diálogos del ingles al español"
    # " vas a traducir diálogos del ingles al español y el resultado debe de ser mayoritariamente compatible con el formato ASCII, en caso de haber caracteres no compatibles, usa sus equivalencias en ascii y al encontrar símbolos no compatibles ignorarlos, no uses símbolos de cierre como apertura, mantén discreto la falta de ellos si no es posible remplazarlos ignóralos"
    " Manten los nombres de los personajes y lugares iguales, no los traduzcas ni los alteres"
    " No traduzcas comandos ni símbolos especiales. Devuelve todo el texto conservando los símbolos exactamente iguales, sin modificaciones"
    " si hay símbolos en todas partes del dialogo quiere decir que son parte del dialogo, quiere decir que son parte del dialogo"
    " Hay comandos en los diálogos! ten cuidado con esos comandos, entre ellos están:"
    " \\\\XX <- cuanto están estas barras los 2 siguiente caracteres que pueden ser mayúsculas y minúsculas son parte del comando, déjalos tal cual igual"
    " $~X y ~X <- esto es un parámetro, no lo modifiques; ^X <- esto también es otro comando, no lo modifiques"
    " algunos diálogos al final tienen sufijos al final del text como '/', '%' u '/%' consérvelos en el texto al final sin alterar su posición"
    " Si consigues formatos asi: [N:TEXTO] solo traduce el texto"
    " si llegas a conseguir un dialogo sin espacios, comandos ni símbolos que esta todo en minúscula déjalo tal cual y si trae '_' con mas razón déjalo igual"
    " los textos de las traducciones no pueden ser mas grandes que el el original, para evitar desbordamiento se recomiendo que sea igual de largo o mas corto que el original"
    " devolverás los json exactamente con este formato para ser parseado:\n\n"

"""
{ 
    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",
    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",
    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",
    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",
    "[Nombre de la clave tal cual como esta]": "[Contenido de la clave ya traducido]",
    ...
}
"""
)

def applyStrings(fixMode: bool = False):

    # InputStrings = open(route_strings_file, "r", encoding="utf8").readlines()
    origin_strings = route_strings_file

    if fixMode:
        origin_strings = route_strings_result_file
        

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print(f"Datos del archivo '{route_output_file}' no es un json")
            return
    
    with open(origin_strings, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputStrings = json.loads(stringOutputData)["Strings"]
        else: 
            print(f"Datos del archivo '{origin_strings}' no es un json")
            return
    
    OutputStrings = open(route_strings_result_file, "w",  encoding="utf8")
    
    nextWord = ""
    ResultText = []

    print("Aplicando cambios")

    def checkCommands(newDialog:str, oldDialog:str):
        _beforeTokens = ["\\", "*"]
        _afterTokens = ["/%", "/"]


        Result = newDialog

        for _bef in _beforeTokens:
            if oldDialog.strip()[:len(_bef)] == _bef:
                if Result.strip()[:len(_bef)] != _bef:
                    Result = f"{_bef}{Result}"
                    break
        for _aff in _afterTokens:
            if oldDialog.strip()[-len(_aff):] == _aff:
                if Result.strip()[-len(_aff):] != _aff:
                    Result = f"{Result}{_aff}".replace("//%", "/%")
                    break
        

        return Result

    for i in InputStrings:

        if nextWord:
            if nextWord.count(" ") != 0:
                if str(i).count(" ") == 0:
                    nextWord = i
                    ResultText.append(nextWord)
                    nextWord = ""
                    continue

            ResultText.append(checkCommands(nextWord, i))
            nextWord = ""
            continue

        t = i

        if t in InputData:

            nextWord = str(InputData[t])

            # if (nextWord.count(" ") == 0):
            #     nextWord = ""

        ResultText.append(i)
        
        pass

    OutputStrings.write(json.dumps({
        "Strings": ResultText
    }, indent=4, ensure_ascii=False))
    if fixMode:
        print("Se ha actualizado los strings exitosamente")
        return
    print("Los cambios han sido aplicados")


    pass

def useTranslate(CHUNKS = 200, restart = False):
    


    # # cliente = genai.configure(api_key= "")
    
    # INDEX = 0

    # if not Chats:

    #     for x in ApiKeys:

    #         INDEX += 1
    #         print(f"cargando modelo de la api {INDEX}")

    #         cliente = genai.Client(api_key= x)

    #         # model = genai.GenerativeModel('gemini-2.0-flash')
    #         # chat = model.start_chat()

    #         while True:

    #             try: 
    #                 chat = cliente.chats.create(model="gemini-2.5-flash")
    #                 response = chat.send_message(prompt)
    #                 print(
    #                     f"Api {INDEX} Conectada exitosamente",
    #                     response
    #                 )
    #                 Chats.append(chat)
    #                 break
    #             except:
    #                 print("re-intentnado")
    #                 pass
        


    # CHUNCKS = 200
    INDEX = 0

    


    with open(route_input_file, 'r', encoding='utf-8') as f:
        inputData = json.load(f)

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            OutputData = json.loads(stringOutputData)
        else: 
            OutputData = {}


    
    INDEX = len(list(OutputData))
    EOF = len(list(inputData))

    


    def _if(cond, _dif, _delse):
        if cond:
            return _dif
        else:
            return _delse

    _cache_data = []

    INDEX = 0
    _cache_data = []
    _cache_faltante = {}
    for i in inputData:
        if OutputData.get(i, False) == False:
            _cache_data.append(i)
            _cache_faltante[i] = inputData[i]
    EOF = len(list(_cache_data))
    _hecho = {}
    _BeforeIndex = 0
    _try = 0

    if not restart:

        print(_cache_faltante)
        print("starting...")
    else: 
        print("restarting...")
    while True:
        _BeforeIndex = INDEX
        print(f"process: {INDEX}/{EOF} intento: {_try+1}")

        if EOF == 0:
            print("Todos los diálogos están traducidos")
            break

        if _try >= 5:
            print("la cadena ha llegado al limite de intentos, volver a intentar mas tarde")
            break

        pass_data = {}
        divider =  _if(_try == 0, 1, 2)

        for i in _cache_data[INDEX:][:int(CHUNKS/(_try+1))]:

            pass_data[i] = inputData[i]
        
        try:
            resp = translate(pass_data)
            _try = 0
        except Exception as e:
            print("error:", e)
            _try += 1
            print("3 segundos de espera antes del reintento")
            time.sleep(3)
            continue
        OutputData = {
            **OutputData, **resp
        }

        _hecho = {
            **_hecho, **resp
        }

        INDEX = len(list(_hecho))

        if INDEX == _BeforeIndex:
            return useTranslate(CHUNKS, True)

        with open(route_output_file, "w", encoding="utf-8") as writeFile:
            writeFile.write(
                json.dumps(OutputData, indent=4)
            )
            pass

        print(f"7 segundos de espera antes del siguiente, proceso: {INDEX}/{EOF}")
        time.sleep(7)
        if INDEX >= EOF:
            print("Traducción de diálogos finalizados correctamente")
            break


def normaliceText(texto):

    # Normalizar el texto a la forma NFKD (descomposición de compatibilidad)
    texto_normalizado = unicodedata.normalize('NFKD', texto)
    
    # Filtrar solo caracteres ASCII, reemplazando los no compatibles
    texto_limpio = texto_normalizado.encode('ASCII', 'ignore').decode('ASCII')
    
    return texto_limpio
    


def cleanValues():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    Blacklist = ["traduccion_", "Traducci\u00f3n ", "Traducci\u00f3n_"]
    OutputData = {}

    print("limpiando...")

    for i in InputData:

        key = i

        for x in Blacklist:

            if key[:len(x)] == x:
                key = key[len(x):]
            pass
        
        OutputData[key] = InputData[i]

        pass

    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print("Limpieza completa!")

    pass

def cleanVoid():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_input_file, 'r', encoding='utf-8') as f:
        stringOriginalData = f.read()
        InputDataOriginal = json.loads(stringOriginalData)

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    OutputData = {}
    count = 0

    print("Eliminando espacios vacios...")

    for i in InputData:

        cadena = str(InputData[i]).strip()
        cadenaOriginal = str(InputDataOriginal.get(i, "-TTT-")).strip()

        if cadena == "":
            if cadenaOriginal != "":
                count +=1
                continue
        
        if cadena[:1] == "\\":
            if "*" in cadena.strip()[3:5]:
                _test = clean_codes(cadena[5:]).replace(" ", "")
                if len(_test) < 4:
                    count +=1
                    continue
                pass

        if cadena[:1] == "*":
            if "*" in cadena.strip()[1:4]:
                _test = clean_codes(cadena[4:]).replace(" ", "")
                if len(_test) < 3:
                    count +=1
                    continue
                pass
        
        
        OutputData[i] = InputData[i]

        pass

    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print(f"{count} Espacios vacíos han sido eliminados!")

    pass


def clean_codes(texto):
    # Elimina todo excepto letras (mayúsculas y minúsculas), números y espacios
    texto_limpio = re.sub(r'[^\w\s]', '', texto)
    # Opcional: si quieres quitar también los números, usa:
    # texto_limpio = re.sub(r'[^a-zA-Z\s]', '', texto)
    return texto_limpio

def merge():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_input_file, 'r', encoding='utf-8') as f:
        stringOriginalData = f.read()
        InputDataOriginal = json.loads(stringOriginalData)

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    OutputData = {}

    print("Aplicando cambios")

    for i in InputDataOriginal:
        OutputData[i] = InputDataOriginal[i]
    for i in InputData:
        OutputData[i] = InputData[i]
    


    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print(f"los cambios han combinados correctamente")

    pass

def manualGenerate():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_input_file, 'r', encoding='utf-8') as f:
        stringOriginalData = f.read()
        InputDataOriginal = json.loads(stringOriginalData)

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    OutputData = {}

    print("Generando archivo de dialogos no traducidos")

    for i in InputDataOriginal:
        
        if not i in InputData:
            OutputData[i] = InputDataOriginal[i]
    


    with open(route_manual_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print(f"archivo manual generado, puedes ver los dialogos faltantes en '{route_manual_file}'")

    pass

def View():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_input_file, 'r', encoding='utf-8') as f:
        stringOriginalData = f.read()
        InputDataOriginal = json.loads(stringOriginalData)

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    OutputData = {}
    count = 0


    for i in InputDataOriginal:
        
        if not i in InputData:
            OutputData[i] = InputDataOriginal[i]
            count+=1
    
    print(f"el numero de dialogos totales son: {len(list(InputDataOriginal))}")
    print(f"el numero de dialogos ya traducidos son: {len(list(InputData))}")
    print(f"el numero de dialogos que faltan por traducir son: {len(list(OutputData))}")

    pass


def manualApply():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_output_file, 'r', encoding='utf-8') as f:
        stringOriginalData = f.read()
        InputData = json.loads(stringOriginalData)

    if not os.path.exists(route_manual_file):

        t = open(route_manual_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()
    with open(route_manual_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputDataManual = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    
    OutputData = {}

    print("Aplicando cambios manuales")

    for i in InputData:
        OutputData[i] = InputData[i]
    for i in InputDataManual:
        OutputData[i] = InputDataManual[i]
    


    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print(f"los cambios manuales han combinados correctamente")

    pass

def loadMap() -> list[str]:

    

    with open(route_map_file, 'r', encoding='utf-8') as f:
        inputData = json.load(f)


    return inputData.get("map", [])

def GenMap(): # GenMap esta deprecado en su lugar usar GenerateInput

    if os.path.exists(route_map_file):
        print("el archivo de mapeo ya existe")
        return False
    
    if not os.path.exists(route_ja_input_file):
        print(f"el archivo del cual parte el mapeo '{route_ja_input_file}' no existe ")
        return False
    
    

    with open(route_ja_input_file, 'r', encoding='utf-8') as f:
        inputData: dict = json.load(f)


    OutputData = {
        "map": list(inputData.keys())
    }

    with open(route_map_file, 'w', encoding='utf-8') as f:
        
        data= json.dumps(OutputData, indent=4)

        f.write(data)
    
    print(f"Se ha generado el archivo de mapeo: '{route_map_file}'")



    return True

def GenerateInput():


    # Maps = loadMap()

    with open(route_strings_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputStrings: list[str] = json.loads(stringOutputData)["Strings"]
        else: 
            print(f"Datos del archivo '{route_strings_file}' no es un json")
            return
    
    OutputData = {}
    addKey = ""

    id_pattern = re.compile(r'^([a-zA-Z0-9_]+_slash_[a-zA-Z0-9_]+_gml_\d+_\d+)(?:_\w+)?$')

    for i in InputStrings:

        if id_pattern.match(i):
            

            addKey = str(i)
            continue

        if addKey:
            if "gml_Script_scr_" in str(i):
                addKey = ""

                continue
            if i == str(i).lower():
                if i.count(" ") == 0:
                    addKey = ""
                    continue
            OutputData[addKey] = i
            addKey = ""
            continue

        # if i in Maps:

        #     addKey = str(i)
        #     continue

        # if addKey:
            
        #     OutputData[addKey] = i
        #     addKey = ""
        #     continue



        
        
        pass

    with open(route_input_file, "w", encoding="utf8") as f:
        a = json.dumps(OutputData, indent=4, sort_keys=False)
        f.write(a)
    
    print("se ha generado el archivo input, ya puede empezar a traducir!")

    

    pass

def cleanNormalice():

    if not os.path.exists(route_output_file):

        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()

    with open(route_output_file, 'r', encoding='utf-8') as f:

        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
    OutputData = {}

    print("Normalizando...")

    for i in InputData:

        
        try:
            OutputData[i] = normaliceText(InputData[i])
        except Exception as e:

            print(f"el dialogo {i} no es un string:", InputData[i])
        pass

    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4)
        )
        pass

    print("Normalización completa!")



def showExtremes(string: str, margin:int = 10):

    return f"{repr(string[:margin])} - {repr(string[-margin:])}"


def str2json(response: str):

    _original = response

    # response = response.split("```")[1]
    response = response.replace("`", "")

    while response[:1] != "{":
        response = response[1:]
        if not response:
            raise Exception("Respuesta no es un json: " + _original)
    while response[-1:] != "}":
        response = response[:-1]
        if response[-2:] != '",':
            response = response[:-1] + "}"
            break
        if not response:
            raise Exception("Respuesta no es un json: " + _original)
            # raise "Respuesta no es un json: " + _original
    
    while True:
        try:
            return json.loads(normaliceText(response))
        except:
            print("reduciendo...", showExtremes(response))
            pass

        while response[-2:] != '",':
            response = response[:-1]
            if not response:
                raise Exception("Respuesta no es un json: " + _original)


        response = response[:-1] + "}"

def newStr2Json(response: str) -> dict[str, str]:

    json_limpio = response.strip("```json").strip("```").strip()

    while True:
        try:
            data = json.loads(json_limpio)
            return data
        except Exception as e:

            while json_limpio[-2:] != '",':
                json_limpio = json_limpio[:-1]
                if not json_limpio:
                    print("Respuesta:", response)
                    raise Exception("error: no es un json", *e.args)
            json_limpio = json_limpio[:-1] + "}"
            print("reduciendo...", showExtremes(json_limpio))

            if not json_limpio:
                print("Respuesta:", response)
                raise Exception("error: no es un json", *e.args)

def translate(data: dict):
    global SwitchIndex

    trys = 3
    response = None  # 1. Inicializamos en None para evitar el error de variable no asociada

    while True:
        try:
            # 2. 💡 Movemos la definición del chat AQUÍ ADENTRO. 
            # Así, si 'SwitchIndex' cambia tras un error, el siguiente intento usará la NUEVA API Key.
            index= SwitchIndex % len(ApiKeys)
            key = ApiKeys[index]
            print(f"generando Bloque con la api {index}: {key}")

            cliente = genai.Client(api_key= key)

            # model = genai.GenerativeModel('gemini-2.0-flash')
            # chat = model.start_chat()

            chat = cliente.chats.create(model="gemini-2.5-flash")
            response = chat.send_message(
                f"{prompt}"
                f"{json.dumps(data, indent=4)}"
            )
            # Chats.append(chat)


            
            # response = chat.send_message(json.dumps(data, indent=4))
            break  # Éxito: salimos del bucle while
            
        except Exception as e:
            print(f"error:", e)
            if not trys:
                print("Se agotaron los intentos para este bloque de diálogos.")
                break  # Fallaron todos los intentos: salimos del bucle
                
            print(f"intento {trys}, reintentando la solicitud con otra API Key...")
            trys -= 1
            SwitchIndex += 1  # Cambiamos de API Key
            time.sleep(3)

    # 3. Avanzamos el índice para el próximo bloque global si todo salió bien
    SwitchIndex += 1

    # 4. Validamos de forma segura si logramos obtener una respuesta
    if response is not None and response.candidates and response.candidates[0].content.parts: #type: ignore
        # Usamos la extracción quirúrgica de la nueva SDK limpia de Markdown
        texto_puro: str = response.candidates[0].content.parts[0].text #type: ignore
        # texto_limpio = re.sub(r"```json\s*|```", "", texto_puro).strip()
        return newStr2Json(texto_puro)
    else:
        # Si falló, lanzamos una excepción controlada para que tu bucle principal 'while' en useTranslate 
        # lo capture en su propio try-except, espere, y lo vuelva a intentar sin perder el progreso.
        raise RuntimeError("No se pudo obtener respuesta de ninguna API Key en este bloque.")


def normaliceTextNew(texto, secure: bool):
    if not isinstance(texto, str):
        return texto
        
    # Reemplazar comillas curvas tipográficas que las IA meten por inercia
    texto_limpio = texto.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    
    # Aquí puedes añadir mapeos manuales si tu fuente de GameMaker requiere algo específico,
    # pero NO uses .encode('ASCII', 'ignore') porque eso borra las tildes y signos de apertura.

    if secure:
        # 2. Diccionario de equivalencias para GameMaker (Rango ASCII Inglés)
        # Reemplaza los caracteres con tilde por su versión limpia y remueve signos de apertura
        reemplazos = {
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N',
            'ü': 'u', 'Ü': 'U',
            '¡': '',  # GameMaker inglés no tiene el signo de apertura, lo removemos
            '¿': ''   # Lo mismo para la interrogación de apertura
        }
        
        # Aplicamos los reemplazos uno a uno
        for original, limpio in reemplazos.items():
            texto = texto.replace(original, limpio)
            
        # 3. Forzar compatibilidad ASCII pura por si se coló algún otro carácter extraño
        texto_normalizado = unicodedata.normalize('NFKD', texto)
        texto_ascii = texto_normalizado.encode('ASCII', 'ignore').decode('ASCII')
        
        return texto_ascii
    
    return texto_limpio

def cleanNormaliceNew(secure: bool = False):
    if not os.path.exists(route_output_file):
        t = open(route_output_file, "w", encoding="utf-8")
        t.write("{}")
        t.close()

    with open(route_output_file, 'r', encoding='utf-8') as f:
        stringOutputData = f.read()
        if stringOutputData[:1] + stringOutputData[-1:] == "{}":
            InputData = json.loads(stringOutputData)
        else: 
            print("Datos del archivo no es un json")
            return
            
    OutputData = {}
    print("Normalizando strings para GameMaker...")

    for i in InputData:
        try:
            OutputData[i] = normaliceTextNew(InputData[i], secure)
        except Exception as e:
            print(f"el dialogo {i} no es un string:", InputData[i])

    # 💡 CLAVE MAESTRA: ensure_ascii=False
    # Esto obliga a Python a guardar los caracteres reales (¡, ¿, é, ñ) 
    # en lugar de códigos tipo \u00a1 en el archivo JSON definitivo.
    with open(route_output_file, "w", encoding="utf-8") as writeFile:
        writeFile.write(
            json.dumps(OutputData, indent=4, ensure_ascii=False)
        )

    print("¡Normalización real y preservativa completa!")


def help():

    print("""
Requerimientos:
tener en la misma carpeta los siguientes archivos:

(Haz un respaldo del juego antes de operar)
strings.json (el archivo de todos los strings del data.win usa UndertaleModTool para esto, a partir de este se sacara los dialogos en ingles)
lang_ja.json (El archivo de traduccion japones, el cual sera usado para un mapeo de los dialogos)
      
map_key.json (es el archivo de mapeo es necesario para que el programa encuentre los dialogos en 'strings.json', este se genera automáticamente en caso de no existir)

sintaxis:

      dts input-generate (esto va a generar un archivo 'lang_input.json' de la cual a partir de estos diálogos se va a traducir el juego)

      dts run (ejecuta el programa en modo de traducción, tras eso generara un 'lang_es_out.json' en requerido el 'lang_input.json' antes)

      dts voids (eliminara todos los espacios vacios, en caso de que estas sean 0 lineas, la traduccion esta completa, de lo contrario ejecutar 'dts' nuevamente)
      
      dts normalice (normaliza las strings para hacerlas compatibles con el formato de destino)
      dts normalice secure (normaliza las strings para hacerlas compatibles con el formato de destino eliminando tildes y caracteres especiales)
          
      dts normalice-old (normaliza las strings para hacerlas compatibles con el formato de destino) (Deprecado)
      
      dts merge (combina los cambios y te genera un archivo lang_es_out.json listo para incrustar)

      dts apply (este aplicara todos los cambios al archivo string.txt y generara otro llamado 'string_es.txt')
      dts fix (este actualizara todos los cambios resueltos al archivo 'string_es.txt')

      dts pull-manual (genera un archivo 'lang_manual_edit.json' donde se encuentra los diálogos que no se pueden traducir automáticamente)

      dts apply-manual (aplica los cambios de 'lang_manual_edit.json' al archivo final)

      dts view (Muestra información del progreso)
      
""")





if "__main__" == __name__:

    # GenMap()

    long = len(sys.argv)
    
    if long == 1:
        help()
    elif long > 1:
        if sys.argv[1] == "clean":
            cleanValues()
        elif sys.argv[1] == "voids":
            cleanVoid()
        elif sys.argv[1] == "normalice":
            if long == 3:
                if sys.argv[2] == "secure":
                    print("Normalización en modo seguro")
                    cleanNormaliceNew(True)
            else:
                cleanNormaliceNew()
        elif sys.argv[1] == "normalice-old":
            cleanNormalice()
        elif sys.argv[1] == "merge":
            merge()
        elif sys.argv[1] == "apply":
            applyStrings()
        elif sys.argv[1] == "fix":
            applyStrings(True)
        elif sys.argv[1] == "pull-manual":
            manualGenerate()
        elif sys.argv[1] == "apply-manual":
            manualApply()
        elif sys.argv[1] == "view":
            View()
        elif sys.argv[1] == "input-generate":
            GenerateInput()
        elif sys.argv[1] == "run":
            useTranslate(100)
        else:
            print(f"{sys.argv[1]} no es un comando reconocido, por favor usar help para conocer mas")
        
            
        
        
        
        
