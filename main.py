from lxml import etree
import re
from py2neo import Graph,Node, Relationship

graph = Graph(uri="neo4j://localhost:7687", auth=("neo4j", "12345678"))

root = etree.parse("30041719_DIN_EN_1991-4.xml")
mml = '{http://www.w3.org/1998/Math/MathML}'
list_of_words_of_method1 = ['mit', 'Dabei ist', 'Darin ist', 'mit der Federzahl,', 'mit:', 'Daraus ergibt',
                            'Daraus ergibt sich die Federgleichung']
list_of_math_operators = ['+', '-', '/', '·', '×', '−', '±', 'pow', '⋅', ]
expression_for_formulas='.//disp-formula[@id]'


def is_integar(n):
    '''
    to check if the input is integar or not
    :param n: element of equations
    :return: True : if the number is integar
    '''
    try:
        int(n)
        return True
    except ValueError:
        return False
def is_float(n):
    '''
        to check if the input is float or not
        :param n: element of equations
        :return: True : if the number is float
        '''
    if "," in n:
        n = n.replace(",", ".")
    try:
        float(n)
        return True
    except ValueError:
        return False
def check_tag(element):
    '''
    This function checks if a MathML tag is followed by a mathematical operator.

    :param element: MathML tag
    :return: True if the tag is not followed by any mathematical operator
    '''

    def is_math_operator(node):
        return node.tag == (mml + 'mo') and node.text not in {'+', '-', '−', '∑', 'cos', 'sin'}

    def is_valid_fenced(node):
        return node.tag == (mml + 'mfenced') and all(child.tag != (mml + 'mfrac') and child.tag != (mml + 'msqrt') and child.tag != (mml + 'mo') for child in node)

    if element.getnext() is not None:
        if element.tag == (mml + 'mstyle') and ('max' in element.itertext() or 'min' in element.itertext()):
            return False
        if is_math_operator(element.getnext()):
            return False
        if element.getnext().tag == (mml + 'mspace'):
            next_node = element.getnext().getnext()
            if next_node is not None:
                if is_math_operator(next_node):
                    return False
                elif is_valid_fenced(next_node) and all(is_math_operator(child) for child in next_node):
                    return False
        elif is_valid_fenced(element.getnext()):
            if all(is_math_operator(child) for child in element.getnext()):
                return False
        elif element.tag == (mml + 'mstyle') and element.getnext().tag == (mml + 'msub'):
            return False
        else:
            return True

    return False
def converting_mathml_to_plain_text(element):
    '''
    convert MathML tags into plain text (like pdf format)
    :param element: MathML Tag
    :return: Plain text
    '''

    if element.tag == (mml + 'mspace'):
        return ''

    elif element.tag == (mml + 'mo'):
        if (element.getparent() is not None and element.getparent().tag == (mml + 'munderover')) or (
                element.getparent() is not None and element.getparent().getparent() is not None and element.getparent().getparent().tag == (
                mml + 'munderover')):
            return '.'
        elif element.text == ',':
            if element.getparent().tag == (mml + 'math'):
                if element.getnext() is not None and element.getnext().tag == (mml + 'msub') and element.getnext()[
                    0].tag == (mml + 'mspace'):
                    return ','
                else:
                    return 'oder'

            elif element.getprevious() is not None and element.getprevious().tag == (
                    mml + 'mfrac') and element.getparent().tag == (mml + 'mfenced'):
                return '.'
            else:
                return element.text
        elif element.getparent().tag == (mml + 'mrow') and element.getparent().getparent().tag == (mml + 'msub'):
            return ' '
        elif element.text == '〈' or element.text == '〉':
            return ''
        elif element.text == '|' and element.getnext() is not None and element.getnext().getnext() is not None and element.getnext().getnext().tag != (
                mml + 'mo'):
            return element.text + '.'

        else:
            return element.text

    elif element.tag == (mml + 'mi'):
         return element.text

    elif element.tag == (mml + 'mtext'):
        if element.text == 'in' and element.getparent() == (mml + 'math'):
            result = 'für'
        else:
            result = element.text
        return result

    elif element.tag == (mml + 'mn'):
        result = element.text
        if element.getparent().tag == (mml + 'math') and element.getnext() is not None and element.getnext().tag != (
                mml + 'mspace'):
            return result + '.'
        else:
            return result


    elif element.tag == (mml + 'msub'):
        if element.find(mml + 'mfenced') is not None:
            result = converting_mathml_to_plain_text(element[0]) + '.' + converting_mathml_to_plain_text(element[1])
        else:

            result = converting_mathml_to_plain_text(element[0]) + '(' + converting_mathml_to_plain_text(
                element[1]) + ')'
        return result


    elif element.tag == (mml + 'mstyle') or element.tag == (mml + 'mover') or element.tag == (mml + 'mtr') or element.tag == (mml + 'mtable') :
        result = ''
        for ele in element.iterchildren():
            result = result + converting_mathml_to_plain_text(ele)
        return result

    elif element.tag == (mml + 'mfrac'):
        if element.getparent() is not None and element.getparent().tag == (mml + 'msub') and element.getnext() is None:
            result = converting_mathml_to_plain_text(element[0]) + '|' + converting_mathml_to_plain_text(element[1])
        elif element.getnext() is not None and element.getnext().tag == (mml + 'mfenced'):
            result = converting_mathml_to_plain_text(element[0]) + '|' + converting_mathml_to_plain_text(
                element[1]) + '.'
        else:
            result = converting_mathml_to_plain_text(element[0]) + '/' + converting_mathml_to_plain_text(element[1])
        return result

    elif element.tag == (mml + 'mrow'):
        result = ''
        if element.getparent() is not None and (
                element.getparent().tag == (mml + 'msub') or element.getparent().tag == (mml + 'msubsup')):
            for ele in element.iterchildren():
                result = result + str(converting_mathml_to_plain_text(ele))
        else:
            for ele in element.iterchildren():
                if check_tag(ele) == True:
                    result = result + str(converting_mathml_to_plain_text(ele)) + '.'
                else:
                    result = result + str(converting_mathml_to_plain_text(ele))
        if result:
            return result
        else:
            return ''

    elif element.tag == (mml + 'mmultiscripts'):
        result = ''
        for ele in element.iterchildren():
            result = result + converting_mathml_to_plain_text(ele)
        return result + ')'

    elif element.tag == (mml + 'mprescripts'):
        return '('

    elif element.tag == (mml + 'mroot'):
        result = converting_mathml_to_plain_text(element[0]) + 'root' + converting_mathml_to_plain_text(element[1])
        return result

    elif element.tag == (mml + 'mfenced'):
        result = ''
        for ele in element.getchildren():
            if check_tag(ele) == True:
                result = result + converting_mathml_to_plain_text(ele) + '.'

            elif converting_mathml_to_plain_text(ele):

                result = result + converting_mathml_to_plain_text(ele)
        if element.get('open') == '|':
            return result
        elif element.getparent().tag == (mml + 'mfenced'):
            return element.get('open') + result + element.get('close') + '.'
        else:
            return element.get('open') + result + element.get('close')



    elif element.tag == (mml + 'msup'):
        if element[0].tag == (mml + 'mn') and (element[1].tag == (mml + 'mn') or element[1].text == '*'):
            result = converting_mathml_to_plain_text(element[0]) + '^' + converting_mathml_to_plain_text(element[1])
        else:
            result = converting_mathml_to_plain_text(element[0]) + ' pow ' + converting_mathml_to_plain_text(element[1])
        return result

    elif element.tag == (mml + 'msubsup'):
        result = converting_mathml_to_plain_text(element[0]) + '(' + converting_mathml_to_plain_text(
            element[1]) + ')' + 'pow' + converting_mathml_to_plain_text(element[2])
        if element[2].tag == (mml + 'mo'):
            return converting_mathml_to_plain_text(element[0]) + '(' + converting_mathml_to_plain_text(
                element[1]) + ')' + '^' + converting_mathml_to_plain_text(element[2])
        else:
            return result

    elif element.tag == (mml + 'munderover'):
        result = 'from' + converting_mathml_to_plain_text(element[1]) + converting_mathml_to_plain_text(
            element[0]) + 'to' + converting_mathml_to_plain_text(element[2]) + '.'
        return result

    elif element.tag == (mml + 'msqrt'):
        result = converting_mathml_to_plain_text(element[0]) + 'sqrt' + '2'
        if element.getprevious() is not None and element.getprevious().tag == (
                mml + 'mi') and element.getparent().tag != (mml + 'mfrac'):
            return '.' + result
        else:
            return result
    elif element.tag == (mml + 'munder'):
        return converting_mathml_to_plain_text(element[1])

    else:
        return element.tag

def extract_equation_sides(content_of_equation):
    '''
    Extract left and right sides of an equation.

    :param equation_string: Equation string containing mathematical operators.
    :return: Left and right sides of the equation.
    '''
    if re.search(r'[=≥≤><≈≅]', content_of_equation):
        # to split formula into left and right side
        if "=" in content_of_equation:
            equation_sides = re.split(r'=', content_of_equation, 1)
            equation_leftside = equation_sides[0]
            equation_rightside = equation_sides[1]
        else:
            equation_sides = re.split(r'[=≥≤><≈≅]', content_of_equation, 1)
            equation_leftside = equation_sides[0]
            equation_rightside = equation_sides[1]
        return equation_leftside, equation_rightside

def removing_surronding_text(content_of_equation):
    '''
    used to remove the surronding text like definition term or post condition
    :param content_of_equation: equation after converted to plain text
    :return: equation after removing the surronding text
    '''
    sides = extract_equation_sides(content_of_equation)
    if sides:
        equation_leftside = sides[0]
        equation_rightside = sides[1]

        if ':' in equation_leftside:
            equation_leftside = equation_leftside.split(':')[1]
            return equation_leftside + '=' + equation_rightside

        else:
            if any([x in equation_leftside for x in list_of_math_operators]):
                if '.' in equation_leftside:
                    equation_leftside = equation_leftside.split('.')[-1]

            return equation_leftside + '=' + equation_rightside

    else:
        return content_of_equation



def equation_validation(content_of_equation):
    '''
    Validate the equation under specification.
    :param content_of_equation: Equation in plain text.
    :return: Valid / Unvalid / Not Valid
    '''
    right_side_valid = False
    left_side_valid = True
    count_of_number = 0
    count_of_symbols = 0
    sides = extract_equation_sides(content_of_equation)
    if sides:
        equation_leftside = sides[0]
        equation_rightside = sides[1]

        if any([x in equation_leftside for x in list_of_math_operators]):
            left_side_valid = False

        if is_integar(equation_leftside) or is_float(equation_leftside):
            left_side_valid = False

        if any([y in equation_rightside for y in list_of_math_operators]):
            list_of_element_of_right_side = re.split(r'≈|=|×|⋅|pow|root|·|−|/|from|to|\+|:|±|≅|\.', equation_rightside)

            for k in range(len(list_of_element_of_right_side)):
                if list_of_element_of_right_side[k].strip():
                    if (is_integar(list_of_element_of_right_side[k]) == True) or (
                            is_float(list_of_element_of_right_side[k]) == True):
                        count_of_number = count_of_number + 1
                    else:
                        count_of_symbols = count_of_symbols + 1

            if (count_of_symbols == 1 and count_of_number >= 1) or (count_of_symbols > 1):
                right_side_valid = True

        if right_side_valid == True and left_side_valid is True:
            return 'Valid'
        elif right_side_valid == False and left_side_valid is True:
            return 'Unvalid'
        else:
            return 'Not Valid'


def removing_boundaries_condition():
    '''
    is used to remove the boundary condations from formula
    :param content_of_equation: text of formula
    :return: dictionary of equations after removing the boundary conditions
    '''
    list_of_boundary_words = ['mit', 'bei', 'für']

    dictionary_before_removing = reformating_formulas()
    dictionary_after_removing = {}
    for key, content_of_equation in dictionary_before_removing.items():
        for i in range(len(list_of_boundary_words)):
            if list_of_boundary_words[i] in content_of_equation:
                content_of_equation = content_of_equation[0:content_of_equation.index(list_of_boundary_words[i])]

        if ':' in content_of_equation:
            content_of_equation = content_of_equation.split(':')[1].strip()
        if 'Falls' in content_of_equation and 'gilt' in content_of_equation:
            index = content_of_equation.find('gilt')
            content_of_equation = content_of_equation[index:]
        if 'falls' in content_of_equation:
            index = content_of_equation.find('falls')
            content_of_equation = content_of_equation[:index]
        if 'wenn' in content_of_equation:
            index = content_of_equation.find('wenn')
            content_of_equation = content_of_equation[:index]

        dictionary_after_removing[key] = content_of_equation

    return dictionary_after_removing
def split_equation_into_elements():
    '''
    to split the equations by mathematical opearators into list of elements

    :return: two dictionaries, first one for valid equations , second one for unvalid equations
    '''
    dictionary_after_split_to_sub_id = split_equation_into_subequations()
    dictionary_of_unvalid_equations = {}
    dictionary_after_split_content = {}
    for key, content_of_equation in dictionary_after_split_to_sub_id[0].items():
        list_of_elements_of_formula = []
        if content_of_equation.strip().startswith('.'):
            content_of_equation = content_of_equation.replace('.', '', 1)

        content_of_equation_after_remove_extra_words = content_of_equation
        sides = extract_equation_sides(content_of_equation_after_remove_extra_words)


        if equation_validation(content_of_equation_after_remove_extra_words) == 'Valid':

            if sides:
                equation_leftside = sides[0]
                equation_rightside = sides[1]
                list_of_elements_of_formula.append(equation_leftside)
                list_of_elements_of_formula.append(equation_rightside)
            dictionary_after_split_content[key] = list_of_elements_of_formula
        elif equation_validation(content_of_equation_after_remove_extra_words) == 'unvalid':
            if sides:
                equation_leftside = sides[0]
                list_of_elements_of_formula.append(equation_leftside)

            dictionary_of_unvalid_equations[key] = list_of_elements_of_formula

    return dictionary_after_split_content, dictionary_of_unvalid_equations


def reformating_formulas():
    '''
    Extract the formulas from the XML files and removing the surronding text
    :return: dictionary of formulas {id:'list_of_elements'}
    '''

    dictionary_of_formulas = {}
    for equation in root.iter('disp-formula'):
        content_of_formula = ''
        if equation.get('id'):
            for mathml in equation.findall(mml + 'math'):
                if mathml is not None:
                    for mathml_tag in mathml.iterchildren():
                        if check_tag(mathml_tag) == True and converting_mathml_to_plain_text(mathml_tag):
                            content_of_formula = content_of_formula + str(
                                converting_mathml_to_plain_text(mathml_tag)) + '.'
                        else:
                            content_of_formula = content_of_formula + str(
                                converting_mathml_to_plain_text(mathml_tag))
        if equation.get('id') is not None:
            dictionary_of_formulas[equation.get('id')] = removing_surronding_text(content_of_formula)

    return dictionary_of_formulas


def split_equation_into_subequations():
    """
    is used to split equation into subequations

    input: dictionary of equations after removing the boundary conditions and surronding text
    :return: list of dictionaries, first dictionary is dictionary of equations after splitting, second dictionary is dictionary of only equations, which are splitted
    """
    dictionry_of_splited_equations = {}
    words_to_split = ["und", "bzw.", "oder"]
    dictionary_of_equation_after_remving = removing_boundaries_condition()
    dictiony_after_splited = {}
    list_of_operator = ["=", "<", ">", "≥", "≤", "≈", "≅"]
    list_of_returned_dictionries = []
    for id, equation in dictionary_of_equation_after_remving.items():
        list_of_splited_equations = []
        count = 0
        equation_after_remove = ""

        for i in range(len(words_to_split)):

            if words_to_split[i] in equation:
                indexx = equation.index(words_to_split[i])
                if (indexx + len(words_to_split[i]) + 1) > len(equation) or indexx == 0:
                    equation_after_remove = equation.replace(words_to_split[i], " ")
                    dictiony_after_splited[id] = equation_after_remove
                    count = 1
                else:

                    equation_split = equation.split(words_to_split[i])
                    for k in range(len(equation_split)):
                        if k == 0:
                            key = id + "." + str(k + 1)
                            dictiony_after_splited[key] = equation_split[k]
                            if equation_split[k].startswith('.'):
                                if equation_validation(equation_split[k][1:]) == 'Valid':
                                    list_of_splited_equations.append(key)
                            else:
                                if equation_validation(equation_split[k]) == 'Valid':
                                    list_of_splited_equations.append(key)
                            count = 1
                        else:
                            if equation[indexx + len(words_to_split[i])] in list_of_operator:

                                left_side = re.split(r'=|≥|≤|<|>|≈|≅ ', equation, 1)[0]
                                key = id + "." + str(k + 1)
                                dictiony_after_splited[key] = left_side + equation_split[k]
                                text = left_side + equation_split[k]
                                if text.startswith('.'):
                                    if equation_validation(text[1:]) == 'Valid':
                                        list_of_splited_equations.append(key)
                                else:
                                    if equation_validation(text) == 'Valid':
                                        list_of_splited_equations.append(key)
                                count = 1

                            elif ('=' or '<' or '>' or '≅' or '≈' or '≤' or '≥') not in equation_split[k]:
                                text = ''
                                key = id + "." + str(k + 1)
                                left_side = re.split(r'=|≥|≤|<|>|≈|≅ ', equation, 1)[0]
                                dictiony_after_splited[key] = left_side + '=' + equation_split[k]
                                text = left_side + '=' + equation_split[k]

                                if text.startswith('.'):
                                    if equation_validation(text[1:]) == 'Valid':
                                        list_of_splited_equations.append(key)
                                else:
                                    if equation_validation(text) == 'Valid':
                                        list_of_splited_equations.append(key)
                                count = 1

                            else:
                                key = id + "." + str(k + 1)
                                dictiony_after_splited[key] = equation_split[k]
                                if equation_split[k].startswith('.'):
                                    if equation_validation(equation_split[k][1:]) == 'Valid':
                                        list_of_splited_equations.append(key)
                                else:
                                    if equation_validation(equation_split[k]) == 'Valid':
                                        list_of_splited_equations.append(key)
                                count = 1
                    dictionry_of_splited_equations[id] = list_of_splited_equations
        if count == 0:
            dictiony_after_splited[id] = equation

    list_of_returned_dictionries.append(dictiony_after_splited)
    list_of_returned_dictionries.append(dictionry_of_splited_equations)
    return list_of_returned_dictionries


def eliminate_brackets(text):
    """
    Eliminate brackets from the given text.

    Args:
        text (str): Input text.

    Returns:
        str: Text with brackets removed.
    """
    if text is not None:

        if text.count('(') != text.count(')'):

            if '(' in text and ')' not in text:
                return eliminate_brackets(text.replace('(', ''))
            elif ')' in text and '(' not in text:
                return eliminate_brackets(text.replace(')', ''))
            elif text.startswith('('):
                return eliminate_brackets(text[1:])
            elif text.endswith(')'):
                return eliminate_brackets(text[:-1])
            elif text.startswith('∑('):
                return eliminate_brackets(text[0:1] + text[2:])
            elif text.startswith('(') and text.endswith(')'):
                return eliminate_brackets(text[1:-1])

            elif '[' in text and ']' not in text:
                return eliminate_brackets(text.replace('[', ''))
            elif ']' in text and '[' not in text:
                return eliminate_brackets(text.replace(']', ''))
            elif text.startswith('['):
                return eliminate_brackets(text[1:])
            elif text.endswith(']') or text.endswith(']]'):
                return eliminate_brackets(text[:-1])
            elif text.startswith('{'):
                return eliminate_brackets(text[1:])
            elif text.endswith('}'):
                return eliminate_brackets(text[:-1])
            else:
                return text
        else:
            if '[' in text and ']' not in text:
                return eliminate_brackets(text.replace('[', ''))
            elif text.startswith('('):
                return eliminate_brackets(text[1:])
            elif ']' in text and '[' not in text:
                return eliminate_brackets(text.replace(']', ''))
            elif text.startswith('['):
                return eliminate_brackets(text[1:])
            elif text.endswith(']') and '[' not in text:
                return eliminate_brackets(text[:-1])
            elif text.startswith('{'):
                return eliminate_brackets(text[1:])
            elif text.endswith('}'):
                return eliminate_brackets(text[:-1])
            else:
                return text


def dictionary_of_equations():
    '''
    use to store the equations with handinlg with the condition of (sin,cos,tan) functions
    :return: dictionary of equations
    '''
    final_dictionary = {}
    for key, value in split_equation_into_elements()[0].items():
        list_of_equation_elements = []
        list_of_equation_elements.append(value[0])
        list_of_rightside_elements = re.split(r'≈|None|≠|×|⋅|pow|=|≥|≤|<|>|≅|root|·|−|/|sqrt|from|to|\+|:|±|\.', value[1])

        for i in list_of_rightside_elements:
            if i.strip():
                text_after = eliminate_brackets(i)
                if is_integar(text_after) == False and is_float(text_after) == False and text_after != 'π':
                    if text_after not in list_of_equation_elements:
                        if '∑' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after[1:])
                        elif 'sin' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after.replace('sin', ''))
                        elif 'cos' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after.replace('cos', ''))
                        elif 'tan' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after.replace('tan', ''))
                        elif '^' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after[:-2])
                        elif 'Δ' in text_after:
                            list_of_equation_elements.append(text_after)
                            list_of_equation_elements.append(text_after.replace('Δ', ''))

                        else:
                            list_of_equation_elements.append(text_after.strip())

        final_dictionary[key] = list_of_equation_elements
    return final_dictionary


def replacing_id_of_equations_with_id_of_subequations(list_of_ids):
    '''
    it is used to replace the ID of equations, which has subequations, with the ID od subequations
    :param list_of_ids: list of ID of equations
    :return:list of equations IDS after modifieded
    '''
    dictionary_of_splited_formula = split_equation_into_subequations()[1]
    list_of_formulas_id = []
    for j in range(len(list_of_ids)):
        if list_of_ids[j] in dictionary_of_splited_formula:
            list_of_formulas_id = list_of_formulas_id + dictionary_of_splited_formula[list_of_ids[j]]
        else:
            list_of_formulas_id.append(list_of_ids[j])
    return list_of_formulas_id

def check_for_relation_for_first_method_relation_for_first_method(list_of_ids):
    '''
    Check if formulas have relations or not.
    :param list_of_ids: List of formulas ids that may have relations.
    :return: Dictionary with primary formula id as key and related formulas as value.
    '''
    dictionay_of_formulas = dictionary_of_equations()
    dictionary_of_primary_formula_and_related_formulas = {}
    list_of_formulas_id = replacing_id_of_equations_with_id_of_subequations(list_of_ids)

    for i in range(len(list_of_formulas_id)):
        for j in range(len(list_of_formulas_id)):
            if list_of_formulas_id[i] in dictionay_of_formulas and list_of_formulas_id[
                j] in dictionay_of_formulas and i != j:
                first_formula_id = list_of_formulas_id[i]
                second_formula_id = list_of_formulas_id[j]
                elements_of_first_formula = dictionay_of_formulas[first_formula_id]
                elements_of_second_formula = dictionay_of_formulas[second_formula_id]

                if elements_of_first_formula[0] in elements_of_second_formula[1:]:
                    if second_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                        dictionary_of_primary_formula_and_related_formulas[second_formula_id] = first_formula_id
                    else:
                        if first_formula_id not in dictionary_of_primary_formula_and_related_formulas[
                            second_formula_id]:
                            dictionary_of_primary_formula_and_related_formulas[
                                second_formula_id] += ',' + first_formula_id

                if elements_of_second_formula[0] in elements_of_first_formula[1:]:
                    if first_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                        dictionary_of_primary_formula_and_related_formulas[first_formula_id] = second_formula_id
                    else:
                        if second_formula_id not in dictionary_of_primary_formula_and_related_formulas[
                            first_formula_id]:
                            dictionary_of_primary_formula_and_related_formulas[
                                first_formula_id] += ',' + second_formula_id

    return dictionary_of_primary_formula_and_related_formulas


def check_for_relation_for_second_method(list_of_dispaly_ids, list_of_refernce_ids):
    '''
    Check the relations between the list of primary formulas and the list of related formulas.
    :param list_of_dispaly_ids: Formulas represented in display-formula tag.
    :param list_of_refernce_ids: Formulas represented in xref tag.
    :return: Dictionary of relations between formulas.
    '''
    dictionay_of_formulas = dictionary_of_equations()
    dictionary_of_primary_formula_and_related_formulas = {}

    list_of_refernce_formulas_ids = replacing_id_of_equations_with_id_of_subequations(list_of_refernce_ids)
    list_of_dispaly_formulas_ids = replacing_id_of_equations_with_id_of_subequations(list_of_dispaly_ids)

    for i in range(len(list_of_dispaly_formulas_ids)):
        for j in range(len(list_of_refernce_formulas_ids)):
            if list_of_dispaly_formulas_ids[i] in dictionay_of_formulas and list_of_refernce_formulas_ids[
                j] in dictionay_of_formulas:
                first_formula_id = list_of_dispaly_formulas_ids[i]
                second_formula_id = list_of_refernce_formulas_ids[j]
                elements_of_first_formula = dictionay_of_formulas[first_formula_id]
                elements_of_second_formula = dictionay_of_formulas[second_formula_id]

                if elements_of_first_formula[0] in elements_of_second_formula[1:]:
                    if second_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                        dictionary_of_primary_formula_and_related_formulas[second_formula_id] = first_formula_id
                    else:
                        if first_formula_id not in dictionary_of_primary_formula_and_related_formulas[second_formula_id]:
                            dictionary_of_primary_formula_and_related_formulas[second_formula_id] += ',' + first_formula_id

                if elements_of_second_formula[0] in elements_of_first_formula[1:]:
                    if first_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                        dictionary_of_primary_formula_and_related_formulas[first_formula_id] = second_formula_id
                    else:
                        if second_formula_id not in dictionary_of_primary_formula_and_related_formulas[first_formula_id]:
                            dictionary_of_primary_formula_and_related_formulas[first_formula_id] += ',' + second_formula_id

    return dictionary_of_primary_formula_and_related_formulas



def check_for_relation_for_third_method(list_of_equations, list_of_related_sections):
    '''
    used to check of relation
    :param list_of_equations: list of displays formulas ids
    :param list_of_related_sections: list of refernces sections id
    :return: dictionary of relation after checking
    '''
    dictionary_of_sec_and_formulas_in_sections = formulas_in_section()
    dictionary_of_primary_formulas_and_related_formulas = {}
    list_of_formulas_in_section = []
    for n in range(len(list_of_related_sections)):
        if list_of_related_sections[n] in dictionary_of_sec_and_formulas_in_sections:
            list_of_formulas_in_section = list_of_formulas_in_section + dictionary_of_sec_and_formulas_in_sections[
                list_of_related_sections[n]]
            dictionary_of_primary_formulas_and_related_formulas = check_for_relation_for_second_method(list_of_equations,
                list_of_formulas_in_section)
    return dictionary_of_primary_formulas_and_related_formulas


def first_method_case_one(formula):
    '''
    to get relations between formulas with specific words, case: the related formulas located in same paragraph
    :param formula: the main formula
    :return: dictionary of main formulas and related formulas
    '''
    list_of_ids_of_formula_in_p_tag = []
    if formula.tail is not None:
        if formula.tail.strip() in list_of_words_of_method1:
            if formula.getparent() is not None:
                for i in formula.getparent().findall(expression_for_formulas):
                    list_of_ids_of_formula_in_p_tag.append(i.get('id'))

    if len(list_of_ids_of_formula_in_p_tag) > 1:
        return check_for_relation_for_first_method_relation_for_first_method(list_of_ids_of_formula_in_p_tag)


def first_method_case_two(formula):
    '''
    to get relations between formulas with specific words , case : the related formulas located in next paragraph
    :param formula: the main formula
    :return: dictionary of main formulas and related formulas

    '''
    list_of_ids_of_formula_in_p_tag = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None and formula.getparent().getnext().text is not None:
        if formula.getparent().getnext().text.strip() in list_of_words_of_method1:

            for formula_in_p in formula.getparent().findall(expression_for_formulas):
                list_of_ids_of_formula_in_p_tag.append(formula_in_p.get('id'))
            for formula_in_next_p in formula.getparent().getnext().findall(expression_for_formulas):
                list_of_ids_of_formula_in_p_tag.append(formula_in_next_p.get('id'))

    if len(list_of_ids_of_formula_in_p_tag) > 1:
        return check_for_relation_for_first_method_relation_for_first_method(list_of_ids_of_formula_in_p_tag)


def first_method_case_three(formula):
    '''
        to get relations between formulas with specific words, case: the specific word located in the text of related formula
        :param formula: the main formula
        :return: dictionary of main formulas and related formulas
    '''
    list_of_ids_of_formula_in_p_tag = []
    if formula.getnext() is not None and formula.getnext().tag == 'disp-formula' and formula.getnext().get(
            'id') is not None:

        if ''.join(formula.getnext().find(mml + 'math').itertext()).strip().startswith('mit'):
            list_of_ids_of_formula_in_p_tag.append(formula.get('id'))
            list_of_ids_of_formula_in_p_tag.append(formula.getnext().get('id'))
    if len(list_of_ids_of_formula_in_p_tag) > 1:
        return check_for_relation_for_first_method_relation_for_first_method(list_of_ids_of_formula_in_p_tag)


def first_method():
    '''
    use to collect all cases of the first method
    :return: dictionary of relations corresponding to first method
    '''
    dictionary_of_relation_depend_on_first_method = {}
    list_of_all_dictionaries = []
    for formula in root.findall(expression_for_formulas):

        if first_method_case_two(formula):
            list_of_all_dictionaries.append(first_method_case_two(formula))
        if first_method_case_one(formula):
            list_of_all_dictionaries.append(first_method_case_one(formula))
        if first_method_case_three(formula):
            list_of_all_dictionaries.append(first_method_case_three(formula))
    for i in range(len(list_of_all_dictionaries)):
        for key, values in list_of_all_dictionaries[i].items():
            if key in dictionary_of_relation_depend_on_first_method:
                if ',' in values:
                    for i in range(len(values.split(','))):
                        if values.split(',')[i] not in dictionary_of_relation_depend_on_first_method[key].split(','):
                            dictionary_of_relation_depend_on_first_method[key] = \
                            dictionary_of_relation_depend_on_first_method[key] + ',' + values.split(',')[i]
                elif values not in dictionary_of_relation_depend_on_first_method[key].split(','):
                    dictionary_of_relation_depend_on_first_method[key] = dictionary_of_relation_depend_on_first_method[
                                                                             key] + ',' + values
            else:
                dictionary_of_relation_depend_on_first_method[key] = values

    return dictionary_of_relation_depend_on_first_method


def second_method_case_one(formula):
    '''
    used to extract relations bewteen fromula in method, which is depends on identifier of related formula
    case :   identifier of related formulas is in pervious p of the parent p of formula
    :param formula: the primary formula
    :return: dictionary of relation between formulas
    '''
    list_of_dispaly_formulas_ids = []
    list_of_refrence_formulas_ids = []
    if formula.getparent() is not None and formula.getparent().getprevious() is not None:

        for equation in formula.getparent().xpath('descendant-or-self::disp-formula[@id]'):
            if equation.get('id') not in list_of_dispaly_formulas_ids:
                # print(equation.get('id'),end='')
                list_of_dispaly_formulas_ids.append(equation.get('id'))
        for related_formula in formula.getparent().getprevious().xpath(
                'descendant-or-self::xref[@ref-type="disp-formula"]'):
            if related_formula.get('rid').count('for') > 1:
                for id in related_formula.get('rid').split(' '):
                    if id not in list_of_dispaly_formulas_ids and id not in list_of_refrence_formulas_ids:
                        list_of_refrence_formulas_ids.append(id)
            else:
                if related_formula.get('rid') not in list_of_dispaly_formulas_ids and related_formula.get(
                        'rid') not in list_of_refrence_formulas_ids:
                    list_of_refrence_formulas_ids.append(related_formula.get('rid'))
    if list_of_dispaly_formulas_ids and list_of_refrence_formulas_ids:
        return check_for_relation_for_second_method(list_of_dispaly_formulas_ids, list_of_refrence_formulas_ids)


def second_method_case_two(formula):
    '''
       used to extract relations bewteen fromula in method, which is depends on identifier of related formula
       case :   identifier of related formulas is in next p of the parent p of formula
       :param formula: the primary formula
       :return: dictionary of relation between formulas
    '''
    list_of_displays_formulas_ids = []
    list_of_refernce_formulas_ids = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None:

        for equation in formula.getparent().xpath('descendant-or-self::disp-formula[@id]'):
            if equation.get('id') not in list_of_displays_formulas_ids:
                list_of_displays_formulas_ids.append(equation.get('id'))
        for related_formula in formula.getparent().getnext().xpath(
                'descendant-or-self::xref[@ref-type="disp-formula"]'):
            if related_formula.get('rid').count('for') > 1:
                for id in related_formula.get('rid').split(' '):
                    if id not in list_of_displays_formulas_ids and id not in list_of_refernce_formulas_ids:
                        list_of_refernce_formulas_ids.append(id)
            else:
                if related_formula.get('rid') not in list_of_displays_formulas_ids and related_formula.get(
                        'rid') not in list_of_refernce_formulas_ids:
                    list_of_refernce_formulas_ids.append(related_formula.get('rid'))
    if list_of_displays_formulas_ids and list_of_refernce_formulas_ids:
        return check_for_relation_for_second_method(list_of_displays_formulas_ids, list_of_refernce_formulas_ids)


def second_method_case_five(formula):
    '''
       used to extract relations bewteen fromula in method, which is depends on identifier of related formula
       case :   identifier of related formulas is in next of next p of the parent p of formula
       :param formula: the primary formula
       :return: dictionary of relation between formulas
    '''
    list_of_displays_formulas_ids = []
    list_of_refernce_formulas_ids = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None and formula.getparent().getnext().getnext() is not None:

        for equation in formula.getparent().findall(expression_for_formulas):
            if equation.get('id') not in list_of_displays_formulas_ids:
                list_of_displays_formulas_ids.append(equation.get('id'))
        for related_formula in formula.getparent().getnext().getnext().xpath(
                'descendant-or-self::xref[@ref-type="disp-formula"]'):
            if related_formula.get('rid').count('for') > 1:
                for id in related_formula.get('rid').split(' '):
                    if id not in list_of_displays_formulas_ids and id not in list_of_refernce_formulas_ids:
                        list_of_refernce_formulas_ids.append(id)
            else:
                if related_formula.get('rid') not in list_of_displays_formulas_ids and related_formula.get(
                        'rid') not in list_of_refernce_formulas_ids:
                    list_of_refernce_formulas_ids.append(related_formula.get('rid'))
    if list_of_displays_formulas_ids and list_of_refernce_formulas_ids:
        return check_for_relation_for_second_method(list_of_displays_formulas_ids, list_of_refernce_formulas_ids)


def second_method_case_three(formula):
    '''
       used to extract relations bewteen fromula in method, which is depends on identifier of related formula
       case :   identifier of related formulas is in the same p of the parent p of formula
       :param formula: the primary formula
       :return: dictionary of relation between formulas
    '''
    list_of_display_formulas_ids = []
    list_of_reference_formulas_ids = []
    if formula.getparent() is not None:
        for equation in formula.getparent().findall(expression_for_formulas):
            if equation.get('id') not in list_of_display_formulas_ids:
                list_of_display_formulas_ids.append(equation.get('id'))
        for related_formula in formula.getparent().xpath('descendant-or-self::xref[@ref-type="disp-formula"]'):
            if related_formula.get('rid').count('for') > 1:
                for id in related_formula.get('rid').split(' '):
                    if id not in list_of_display_formulas_ids and id not in list_of_reference_formulas_ids:
                        list_of_reference_formulas_ids.append(id)
            else:
                if related_formula.get('rid') not in list_of_display_formulas_ids and related_formula.get(
                        'rid') not in list_of_reference_formulas_ids:
                    list_of_reference_formulas_ids.append(related_formula.get('rid'))

    if list_of_reference_formulas_ids and list_of_display_formulas_ids:
        return check_for_relation_for_second_method(list_of_display_formulas_ids, list_of_reference_formulas_ids)


def second_method_case_six(formula):
    '''
    used to extract relations bewteen fromula in method, which is depends on identifier of related formula
    case :   identifier of related formulas is in pervious p of the parent p of formula
    :param formula: the primary formula
    :return: dictionary of relation between formulas
    '''
    list_of_dispaly_formulas_ids = []
    list_of_refrence_formulas_ids = []
    if formula.getparent() is not None and formula.getparent().getprevious() is not None and formula.getparent().getprevious().getprevious() is not None:
        if formula.getparent().getprevious().getprevious().find(
                'xref[@ref-type]') != None and formula.getparent().getprevious().getprevious().find(
            'disp-formula[@id]') == None:

            for equation in formula.getparent().xpath('descendant-or-self::disp-formula[@id]'):
                if equation.get('id') not in list_of_dispaly_formulas_ids:
                    # print(equation.get('id'),end='')
                    list_of_dispaly_formulas_ids.append(equation.get('id'))
            for related_formula in formula.getparent().getprevious().getprevious().xpath(
                    'descendant-or-self::xref[@ref-type="disp-formula"]'):
                if related_formula.get('rid').count('for') > 1:
                    for id in related_formula.get('rid').split(' '):
                        if id not in list_of_dispaly_formulas_ids and id not in list_of_refrence_formulas_ids:
                            list_of_refrence_formulas_ids.append(id)
                else:
                    if related_formula.get('rid') not in list_of_dispaly_formulas_ids and related_formula.get(
                            'rid') not in list_of_refrence_formulas_ids:
                        list_of_refrence_formulas_ids.append(related_formula.get('rid'))
    if list_of_dispaly_formulas_ids and list_of_refrence_formulas_ids:
        return check_for_relation_for_second_method(list_of_dispaly_formulas_ids, list_of_refrence_formulas_ids)


def second_method():
    '''
       used to extract relations bewteen fromula in method, which is depends on identifier of related formula
       :return: dictionary of relation between formulas
    '''
    list_of_all_dictionaries = []

    for formula in root.findall(expression_for_formulas):

        if second_method_case_one(formula):
            second_method_case_one(formula)
            list_of_all_dictionaries.append(second_method_case_one(formula))
        if second_method_case_two(formula):
            list_of_all_dictionaries.append(second_method_case_two(formula))
        if second_method_case_three(formula):
            list_of_all_dictionaries.append(second_method_case_three(formula))
        if second_method_case_six(formula):
            list_of_all_dictionaries.append(second_method_case_six(formula))

    return merge_dictionaries(list_of_all_dictionaries)


def dabei_case():
    '''
        get realtion in case the refernce equations is mentioned with using word Dabei ist or mit for difination list
        :return: dictionary of relation
    '''
    list_dictionary = []
    for p in root.findall('.//p'):
        list_of_display_formulas = []
        list_of_refernce_sections = []
        list_of_refernce_equations = []

        if p.text != None and p.getprevious() != None and (
                p.text == 'Dabei ist' or p.text == 'mit') and p.getprevious().find(mml + 'disp-formula') is None:

            for formula in p.xpath('descendant-or-self::disp-formula[@id]'):
                list_of_display_formulas.append(formula.get('id'))
            for refernce in p.xpath('descendant-or-self::xref'):
                if refernce.get('ref-type') == 'disp-formula':
                    if refernce.get('rid').count('for') > 1:
                        for id in refernce.get('rid').split(' '):
                            if id not in list_of_refernce_equations and id not in list_of_display_formulas:
                                list_of_refernce_equations.append(id)
                    else:
                        if refernce.get('rid') not in list_of_display_formulas and refernce.get(
                                'rid') not in list_of_refernce_equations:
                            list_of_refernce_equations.append(refernce.get('rid'))

                elif refernce.get('ref-type') == 'sec':
                    if refernce.get('rid').count('sub') > 1:
                        for splited_id in refernce.get('rid').split(' '):
                            if splited_id not in list_of_refernce_sections:
                                list_of_refernce_sections.append(splited_id)
                    else:
                            if refernce.get('rid') not in list_of_refernce_sections:
                                list_of_refernce_sections.append(refernce.get('rid'))



        if list_of_display_formulas:
            list_dictionary.append(
                check_for_relation_for_first_method_relation_for_first_method(list_of_display_formulas))

        if list_of_display_formulas and list_of_refernce_equations:
            list_dictionary.append(
                check_for_relation_for_second_method(list_of_display_formulas, list_of_refernce_equations))
        if list_of_display_formulas and list_of_refernce_sections:
            list_dictionary.append(
                check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections))

    return (merge_dictionaries(list_dictionary))


def formulas_in_section():
    """
    in this function we iterate over all section and get all formulas ids
    :return  Dictionary of section and formulas ids
    """
    dictionary_of_each_sec_and_it_formulas = {}
    for child in root.iter('sec'):
        list_of_formulas_ids_in_sec = []
        sec_id = child.get('id')
        for child2 in child.findall(expression_for_formulas):
            if str(child2.get('id')) != "None":
                list_of_formulas_ids_in_sec.append(str(child2.get('id')))
        if list_of_formulas_ids_in_sec:
            dictionary_of_each_sec_and_it_formulas[sec_id] = list_of_formulas_ids_in_sec
    return dictionary_of_each_sec_and_it_formulas


def third_method_case_one(formula):
    '''
    get realtion in case the refernce section is mentioned in the next paragraph of parent paragraph
    :param formula: display-formula
    :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None:
        list_of_display_formulas.append(formula.get('id'))

        for sec_ref in formula.getparent().getnext().xpath('descendant-or-self::xref[@ref-type]'):
            if sec_ref.get('ref-type') == 'sec':

                if sec_ref.get('rid').count('sub') > 1:

                    for spillted_id in sec_ref.get('rid').split(' '):
                        if spillted_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(spillted_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))

        if list_of_display_formulas and list_of_refernce_sections:
            return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method_case_two(formula):
    '''
        get realtion in case the refernce section is mentioned in the same paragraph of parent paragraph
        :param formula: display-formula
        :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None:
        list_of_display_formulas.append(formula.get('id'))
        for sec_ref in formula.getparent().xpath('descendant-or-self::xref[@ref-type]'):
            if sec_ref.get('ref-type') == 'sec':
                if sec_ref.get('rid').count('sub') > 1:
                    for splited_id in sec_ref.get('rid').split(' '):
                        if splited_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(splited_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))
    if list_of_display_formulas and list_of_refernce_sections:
        return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method_case_four(formula):
    '''
        get realtion in case the refernce section is mentioned in the after next paragraph of parent paragraph
        :param formula: display-formula
        :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None and formula.getparent().getnext().getnext() is not None:
        list_of_display_formulas.append(formula.get('id'))

        for sec_ref in formula.getparent().getnext().getnext().xpath('descendant-or-self::xref'):
            if sec_ref.get('ref-type') == 'sec':
                if sec_ref.get('rid').count('sub') > 1:
                    for splited_id in sec_ref.get('rid').split(' '):
                        if splited_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(splited_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))
    if list_of_display_formulas and list_of_refernce_sections:
        return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method_case_five(formula):
    '''
        get realtion in case the refernce section is mentioned in the after after next paragraph of parent paragraph
        :param formula: display-formula
        :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None and formula.getparent().getnext().getnext() is not None and formula.getparent().getnext().getnext().getnext() is not None:
        list_of_display_formulas.append(formula.get('id'))

        for sec_ref in formula.getparent().getnext().getnext().getnext().xpath(
                'descendant-or-self::xref[@ref-type="sec"]'):
            if sec_ref.get('ref-type') == 'sec':
                if sec_ref.get('rid').count('sub') > 1:
                    for splited_id in sec_ref.get('rid').split(' '):
                        if splited_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(splited_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))
    if list_of_display_formulas and list_of_refernce_sections:
        # print(list_of_display_formulas,list_of_refernce_sections)
        return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method_case_six(formula):
    '''
    get realtion in case the refernce section is mentioned in the previous paragraph of parent paragraph
    :param formula: display-formula
    :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None and formula.getparent().getprevious() is not None:
        list_of_display_formulas.append(formula.get('id'))

        for sec_ref in formula.getparent().getprevious().xpath('descendant-or-self::xref[@ref-type="sec"]'):
            if sec_ref.get('ref-type') == 'sec':
                if sec_ref.get('rid').count('sub') > 1:
                    for splited_id in sec_ref.get('rid').split(' '):
                        if splited_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(splited_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))
    if list_of_display_formulas and list_of_refernce_sections:
        return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method_case_seven(formula):
    '''
    get realtion in case the refernce section is mentioned in the next paragraph of parent paragraph
    :param formula: display-formula
    :return: dictionary of relation
    '''
    list_of_display_formulas = []
    list_of_refernce_sections = []
    if formula.getparent() is not None and formula.getparent().getnext() is not None:
        list_of_display_formulas.append(formula.get('id'))

        for sec_ref in formula.getparent().getnext().xpath('descendant-or-self::xref[@ref-type="sec"]'):
            if sec_ref.get('rid') == 'sec':
                if sec_ref.get('rid').count('sub') > 1:
                    for splited_id in sec_ref.get('rid').split(' '):
                        if splited_id not in list_of_refernce_sections:
                            list_of_refernce_sections.append(splited_id)
                else:
                    if sec_ref.get('rid') not in list_of_refernce_sections:
                        list_of_refernce_sections.append(sec_ref.get('rid'))
    if list_of_display_formulas and list_of_refernce_sections:
        return check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_sections)


def third_method():
    '''
          used to extract relations bewteen fromula in method, which is depends on identifier of related section which has related formulas
          :return: dictionary of relation between formulas
    '''
    list_of_all_dictionaries = []
    dictionary_of_relation_depend_on_third_method = final_dictionary = {}
    for formula in root.findall(expression_for_formulas):

        if third_method_case_one(formula):
            list_of_all_dictionaries.append(third_method_case_one(formula))
        if third_method_case_two(formula):
            list_of_all_dictionaries.append(third_method_case_two(formula))
        if third_method_case_four(formula):
            list_of_all_dictionaries.append(third_method_case_four(formula))
        if third_method_case_five(formula):
            list_of_all_dictionaries.append(third_method_case_five(formula))
        if third_method_case_six(formula):
            list_of_all_dictionaries.append(third_method_case_six(formula))

    for i in range(len(list_of_all_dictionaries)):
        # print(list_of_all_dictionaries[i])
        for key, values in list_of_all_dictionaries[i].items():
            if key in final_dictionary:
                if ',' in values:
                    for i in range(len(values.split(','))):
                        if values.split(',')[i] not in final_dictionary[key].split(','):
                            final_dictionary[key] = final_dictionary[key] + ',' + values.split(',')[i]
                elif values not in final_dictionary[key].split(','):
                    final_dictionary[key] = final_dictionary[key] + ',' + values
            else:
                final_dictionary[key] = values

    return dictionary_of_relation_depend_on_third_method


def ohne_in_same_section():
    '''
    is used to get the relations between the equations, which are located in same structural level of the document
    :return: dictionary of relations
    '''

    list_of_all_last_sections = []
    dictionary_of_section_and_equations = formulas_in_section()

    list_of_dictionries = []

    for child in root.findall(expression_for_formulas):  # to get all formula
        last_sec = " "
        list_of_all_sections = []
        for child2 in child.xpath('ancestor-or-self::sec'):  # to get all parent sections

            list_of_all_sections.append(child2)

        if len(list_of_all_sections) > 0:  # to get only first parent sub_section
            last_sec = list_of_all_sections[-1]


        if last_sec.get("id") not in list_of_all_last_sections:
            list_of_all_last_sections.append(last_sec.get('id'))

    for i in range(len(list_of_all_last_sections)):
        if list_of_all_last_sections[
            i] in dictionary_of_section_and_equations:  # to get the equations in this section by equations_in_section function
            value = dictionary_of_section_and_equations[list_of_all_last_sections[i]]

            list_of_dictionries.append(check_for_relation_for_first_method_relation_for_first_method(value))

    return merge_dictionaries(list_of_dictionries)


def anhang():
    '''
       is used to get the relations between the equations, which are located in Anhang section
       :return: dictionary of relations
       '''
    list_of_dictionaries = []
    for child in root.findall('.//app'):
        list_of_display_formulas = []
        list_of_refernce_section = []
        list_of_refernce_formula = []
        if child.find('sec') == None:
            for child1 in child.findall(expression_for_formulas):
                identifier = child1.get('id')
                list_of_display_formulas.append(identifier)
            for ref in child.findall('.//xref'):
                if ref.get('ref-type') == 'disp-formula':
                    if ref.getprevious() is not None and ref.getprevious().tag == 'xref' and ref.getprevious().get(
                            'ref-type') == 'bibr':
                        pass
                    else:
                        if ref.get('rid').count('for') > 1:
                            for identifier in ref.get('rid').split(' '):
                                if identifier not in list_of_refernce_formula and identifier not in list_of_display_formulas:
                                    list_of_refernce_formula.append(identifier)
                        else:
                            if ref.get('rid') not in list_of_display_formulas and ref.get(
                                    'rid') not in list_of_refernce_formula:
                                list_of_refernce_formula.append(ref.get('rid'))

                elif ref.get('ref-type') == 'sec':
                    if ref.getprevious() is not None and ref.getprevious().tag == 'xref' and ref.getprevious().get(
                            'ref-type') == 'bibr':
                        pass
                    else:
                        if ref.get('rid').count('for') > 1:
                            for identifier in ref.get('rid').split(' '):
                                if identifier not in list_of_refernce_section:
                                    list_of_refernce_section.append(identifier)
                        else:
                            if ref.get('rid') not in list_of_refernce_section:
                                list_of_refernce_section.append(ref.get('rid'))

            list_of_dictionaries.append(
                check_for_relation_for_first_method_relation_for_first_method(list_of_display_formulas))
            list_of_dictionaries.append(
                check_for_relation_for_second_method(list_of_display_formulas, list_of_refernce_formula))
            list_of_dictionaries.append(
                check_for_relation_for_third_method(list_of_display_formulas, list_of_refernce_section))
    return merge_dictionaries(list_of_dictionaries)

def dictionary_of_primary_equationa_and_calculated_variable_of_related_equation(dictionary):
    '''
    :param dictionary: This is a combined dictionary generated from combine_dictionaries and describes all relations in the standard.
    :return: A dictionary with all relations and symbols, used for the database.
    '''
    final_dictionary = {}  # Dictionary used in the graphical database
    dict_of_equations = dictionary_of_equations()

    for key, values in dictionary.items():
        list_of_values = values.split(',')

        for value in list_of_values:
            if value in dict_of_equations:
                val = dict_of_equations[value]
                val_left = val[0]

                if key not in final_dictionary:
                    final_dictionary[key] = val_left
                elif val_left not in final_dictionary[key]:
                    final_dictionary[key] += ',' + val_left

    return final_dictionary


def merge_dictionaries(list_of_dictionaries):
    '''
    use to merge list of dictionaries in one dictionary
    :param list_of_dictionaries: list of dictionaries
    :return: one dictionary
    '''
    final_dictionary = {}
    for i in range(len(list_of_dictionaries)):
        # print(list_of_all_dictionaries[i])
        for key, values in list_of_dictionaries[i].items():
            if key in final_dictionary:
                if ',' in values:
                    for i in range(len(values.split(','))):
                        if values.split(',')[i] not in final_dictionary[key]:
                            final_dictionary[key] = final_dictionary[key] + ',' + values.split(',')[i]
                elif values not in final_dictionary[key].split(','):
                    final_dictionary[key] = final_dictionary[key] + ',' + values
            else:
                final_dictionary[key] = values
    return final_dictionary


def combine_dictionary_of_all_methods_exclude_method_five():
    '''
    used to combine all method for extract relation between formulas automated
    :return: dictionary of relations
    '''
    list_of_dictionaries = []
    if first_method():
        list_of_dictionaries.append(first_method())
    if second_method():
        list_of_dictionaries.append(second_method())
    if third_method():
        list_of_dictionaries.append(third_method())
    if dabei_case():
        list_of_dictionaries.append(dabei_case())
    if ohne_in_same_section():
        list_of_dictionaries.append(ohne_in_same_section())
    if anhang():
        list_of_dictionaries.append(anhang())
    return merge_dictionaries(list_of_dictionaries)


def check_for_method_five(list_of_main_section, list_of_another_section, dictionary_of_symbols, current_section):
    '''
    Check for relations using method five.
    :param list_of_main_section: List of equation IDs in the current subsection.
    :param list_of_another_section: List of equation IDs for another subsection.
    :param dictionary_of_symbols: Dictionary with primary equation ID as key and calculated variables of related equations as value.
    :param current_section: Current subsection.
    :return: Dictionary of relations.
    '''
    list_formula_in_main_section = replacing_id_of_equations_with_id_of_subequations(list_of_main_section)
    list_formula_in_another_section = replacing_id_of_equations_with_id_of_subequations(list_of_another_section)
    dictionay_of_formulas = dictionary_of_equations()
    dictionary_of_primary_formula_and_related_formulas = {}
    list_of_invalid = merge_distionary_of_equations_without_id_and_unvalid_equations().get(current_section, [])

    for first_formula_id in list_formula_in_main_section:
        for second_formula_id in list_formula_in_another_section:
            if first_formula_id in dictionay_of_formulas and second_formula_id in dictionay_of_formulas:
                elements_of_first_formula = dictionay_of_formulas[first_formula_id]
                elements_of_second_formula = dictionay_of_formulas[second_formula_id]

                if elements_of_first_formula[0] != elements_of_second_formula[0]:
                    if elements_of_second_formula[0] in elements_of_first_formula[1:]:

                        if first_formula_id in dictionary_of_symbols:
                            if elements_of_second_formula[0] not in dictionary_of_symbols[first_formula_id] and elements_of_second_formula[0] not in list_of_invalid:
                                if first_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                                    dictionary_of_primary_formula_and_related_formulas[first_formula_id] = second_formula_id
                                else:
                                    if second_formula_id not in dictionary_of_primary_formula_and_related_formulas[first_formula_id]:
                                        dictionary_of_primary_formula_and_related_formulas[first_formula_id] += ',' + second_formula_id
                        else:
                            if elements_of_second_formula[0] not in list_of_invalid:
                                if first_formula_id not in dictionary_of_primary_formula_and_related_formulas:
                                    dictionary_of_primary_formula_and_related_formulas[first_formula_id] = second_formula_id
                                else:
                                    if second_formula_id not in dictionary_of_primary_formula_and_related_formulas[first_formula_id]:
                                        dictionary_of_primary_formula_and_related_formulas[first_formula_id] += ',' + second_formula_id

    return dictionary_of_primary_formula_and_related_formulas



def dictionary_of_relations():
    '''
    to create dictionary of relationships to all methods
    :return: dictionary of relations
    '''


    list_of_all_last_sections = []
    dictionary_of_relations = combine_dictionary_of_all_methods_exclude_method_five()
    count = 0
    final_dict = {}

    for sec in root.xpath('descendant-or-self::sec[@id]'):
        if sec.get('id').startswith('sub') and is_integar(sec.get('id')[4]) and sec.get('id') in formulas_in_section():
            list_of_all_last_sections.append(sec)
    list_of_all_last_sections.reverse()

    if len(list_of_all_last_sections) == 0:
        count = 1
    for i in range(len(list_of_all_last_sections)):
        list_of_dictionaries = []

        splited_section = list_of_all_last_sections[i].get('id')
        while splited_section.count('.') >= 1:
            list_of_dictionaries = []
            splited_section = splited_section.rsplit('.', 1)[0]
            list_of_dictionaries.append(dictionary_of_relations)

            if list_of_all_last_sections[i].get(
                    'id') in formulas_in_section() and splited_section in formulas_in_section():
                equations_in_main_section = formulas_in_section()[list_of_all_last_sections[i].get('id')]
                equation_in_related_section = formulas_in_section()[splited_section]
                list_of_dictionaries.append(
                    check_for_method_five(equations_in_main_section, equation_in_related_section,
                                          dictionary_of_primary_equationa_and_calculated_variable_of_related_equation(
                                              dictionary_of_relations), list_of_all_last_sections[i].get('id')))
                dictionary_of_relations = merge_dictionaries(list_of_dictionaries)

        if splited_section.count('.') == 0:
            new_id = splited_section
        else:
            new_id = splited_section.rsplit('.', 1)[0]
        list_of_dictionaries = []

        list_of_dictionaries.append(dictionary_of_relations)

        while int(new_id.split('-')[1]) > 0:

            prefix = 'sub'
            number = new_id.split('-')[1]
            new_number = str(int(number) - 1)
            new_id = f"{prefix}-{new_number}"

            if list_of_all_last_sections[i].get('id') in formulas_in_section() and new_id in formulas_in_section():
                equations_in_main_section = formulas_in_section()[list_of_all_last_sections[i].get('id')]
                equation_in_related_section = formulas_in_section()[new_id]

                list_of_dictionaries.append(
                    check_for_method_five(equations_in_main_section, equation_in_related_section,
                                          dictionary_of_primary_equationa_and_calculated_variable_of_related_equation(
                                              dictionary_of_relations),
                                          list_of_all_last_sections[i].get('id')))

        dictionary_of_relations = merge_dictionaries(list_of_dictionaries)
        final_dict.update(dictionary_of_relations)

    if count == 1:

        return combine_dictionary_of_all_methods_exclude_method_five()
    else:

        return final_dict


def creation_of_dictionary_of_inline_equations_and_display_equations_without_id():
    '''
    create dictionary of inline formulas and dispaly formulas, which have no ID in each subsection
    :return: dictionary, which id of the subsection as key and calculated variable of formulas, which don't have ID
    '''
    list_of_all_last_sections = []
    xpath_expression = "//disp-formula | //inline-formula"
    dictionary_of_inline_formulas_without_id= {}
    for child in root.xpath(xpath_expression):
        if child.get('id') is None:

            list_of_all_sections = []
            for child2 in child.xpath('ancestor-or-self::sec'):  # to get all parent sections

                list_of_all_sections.append(child2)

            if len(list_of_all_sections) > 0:  # to get only first parent sub_section
                last_sec = list_of_all_sections[-1]


            if last_sec not in list_of_all_last_sections:
                list_of_all_last_sections.append(last_sec)

    for sec in list_of_all_last_sections:

        list_of_left_side = []
        for formula in sec.findall('.//inline-formula'):
            if formula.get('id') is None:

                content_of_formula = ''
                for mathml in formula.findall(mml + 'math'):
                    if mathml is not None:
                        for mathml_tag in mathml.iterchildren():
                            if check_tag(mathml_tag) == True and converting_mathml_to_plain_text(mathml_tag):
                                content_of_formula = content_of_formula + str(
                                    converting_mathml_to_plain_text(mathml_tag)) + '.'
                            else:
                                content_of_formula = content_of_formula + str(
                                    converting_mathml_to_plain_text(mathml_tag))

                after_extra_words = removing_surronding_text(content_of_formula)
                if equation_validation(after_extra_words) == 'Valid' or equation_validation(
                        after_extra_words) == 'unvalid':


                    if extract_equation_sides(after_extra_words):
                        equation_leftside = extract_equation_sides(after_extra_words)[0]

                    if equation_leftside and equation_leftside not in list_of_left_side and equation_leftside != '°':
                        if equation_leftside.find('.'):
                            list_of_left_side.append(equation_leftside.split('.')[-1])
                        else:
                            list_of_left_side.append(equation_leftside)


        for equation in sec.findall('.//disp-formula'):

            content_of_equation = ''
            if equation.get('id') is None:
                for mathml in equation.findall(mml + 'math'):
                    if mathml is not None:
                        for mathml_tag in mathml.iterchildren():
                            if check_tag(mathml_tag) == True and converting_mathml_to_plain_text(mathml_tag):
                                content_of_equation = content_of_equation + str(
                                    converting_mathml_to_plain_text(mathml_tag)) + '.'
                            else:
                                content_of_equation = content_of_equation + str(
                                    converting_mathml_to_plain_text(mathml_tag))

                after_extra_words = removing_surronding_text(content_of_equation)
                if equation_validation(after_extra_words) == 'Valid' or equation_validation(
                        after_extra_words) == 'unvalid':

                    if extract_equation_sides(after_extra_words):
                        equation_leftside = extract_equation_sides(after_extra_words)[0]
                    if equation_leftside and equation_leftside not in list_of_left_side and equation_leftside != '°':
                        if equation_leftside.find('.'):
                            list_of_left_side.append(equation_leftside.split('.')[-1])
                        else:
                            list_of_left_side.append(equation_leftside)

        if list_of_left_side:
            dictionary_of_inline_formulas_without_id[sec.get('id')] = list_of_left_side
    return dictionary_of_inline_formulas_without_id


def creation_of_dictionary_of_unvalid_equation():
    '''
    create dictionary of equations,which don't meet the specifications
    :return: dictionary, which section ID as kex and calculated variables of equations, which don't the specifications as value
    '''
    dictionary_of_unvalid = split_equation_into_elements()[1]
    final_dictionary = {}
    for formula in root.findall('.//disp-formula'):
        list_of_all_sections = []
        if formula.get('id') is not None and formula.get('id') in dictionary_of_unvalid:
            # print(formula.get('id'))
            for sec in formula.xpath('ancestor-or-self::sec'):
                list_of_all_sections.append(sec.get('id'))
            if list_of_all_sections:
                if list_of_all_sections[-1] not in final_dictionary:
                    final_dictionary[list_of_all_sections[-1]] = dictionary_of_unvalid[formula.get('id')]
                else:
                    final_dictionary[list_of_all_sections[-1]] = final_dictionary[list_of_all_sections[-1]] + \
                                                                 dictionary_of_unvalid[formula.get('id')]

    return final_dictionary


def merge_distionary_of_equations_without_id_and_unvalid_equations():
    merged_dict = {}

    # Merge dict1 into merged_dict
    for key, value in creation_of_dictionary_of_inline_equations_and_display_equations_without_id().items():
        merged_dict.setdefault(key, []).extend(value)

    # Merge dict2 into merged_dict
    for key, value in creation_of_dictionary_of_unvalid_equation().items():
        merged_dict.setdefault(key, []).extend(value)
    return merged_dict


def querss():
    graph.delete_all()
    c = Node('main', name='ISO 281', )
    dict1 = dictionary_of_relations()
    for key, value in dict1.items():

        symbol_of_a = dictionary_of_equations()[key][0]
        a = Node('Primary_equation_Node', name=key, Calculated_variable=symbol_of_a,
                 Equation=split_equation_into_subequations()[0][key])
        ca = Relationship(c, "has", a)

        graph.create(a)
        graph.create(ca)


        for i in value.split(','):

            symbol_of_b = dictionary_of_equations()[i][0]

            query = "MATCH (n) WHERE n.name = $node_name RETURN n"
            result = graph.run(query, node_name=i)
            existing_node = result.evaluate()
            if existing_node:

                ag = Relationship(a, "has_relation", existing_node)
                graph.create(ag)

            else:
                b = Node('Related_equation_node', name=i, Calculated_variable=symbol_of_b,
                         Equation=split_equation_into_subequations()[0][i])
                graph.create(b)
                ab = Relationship(a, "has_relation", b)
                graph.create(ab)


def graphical_model():
    graph.delete_all()
    c = Node('main', name='DIN_EN_1991-4')
    dict1 = dictionary_of_relations()
    dictionary_of_equation = dictionary_of_equations()

    for key, value in dict1.items():
        symbol_of_a = dictionary_of_equation[key][0]
        a = Node('Primary_equation_Node', name=key, Calculated_variable=symbol_of_a,
                 Equation=split_equation_into_subequations()[0][key])
        ca = Relationship(c, "has", a)
        graph.create(a)
        graph.create(ca)

    for identf, val in dict1.items():
        query = "MATCH (n) WHERE n.name = $node_name RETURN n"
        result = graph.run(query, node_name=identf)
        primary_node = result.evaluate()
        for i in val.split(','):
            symbol_of_b = dictionary_of_equation[i][0]

            query = "MATCH (n) WHERE n.name = $node_nam RETURN n"
            result = graph.run(query, node_nam=i)
            existing_node = result.evaluate()

            if existing_node:
                ag = Relationship(primary_node, "has_relation", existing_node)
                graph.create(ag)
                cg = Relationship(c, "has", existing_node)
                graph.create(cg)
            else:
                b = Node('Related_equation_node', name=i, Calculated_variable=symbol_of_b,
                         Equation=split_equation_into_subequations()[0][i])
                graph.create(b)
                ab = Relationship(primary_node, "has_relation", b)
                cb = Relationship(c, "has", b)
                graph.create(ab)
                graph.create(cb)






print(dictionary_of_relations())



