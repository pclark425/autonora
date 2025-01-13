
import pandas as pd

"""
def score_categories(dataset:pd.DataFrame, categories:pd.DataFrame, *, data_cat_col:str, data_metric_col:str, cat_score_col:str):
Purpose:
    Compute a score for each category, where score = average of data_metric_col for dataset examples in that category
    Also adds two columns n_covered (number) and f_covered (fraction) to categories, showing how much of the dataset this category covers.
Args:
    dataset (DataFrame): A DataFrame with questions and their category memberships.
    categories (DataFrame): A DataFrame with category information.
    data_cat_col (str): The column of dataset containing category membership information, in the form of a JSON array of
   			  	[{index:<category_index>, score:<score>},...]
                        where <score> is 0-1, showing how much this row is a member of the category with category_index
    data_metric_col (str): The dataset metric to average over, when computing the category score
    cat_score_col (str): The category column to place the overall category score in
Returns:
    The categories dataframe, with the cat_score_col column added.
Example:
    dataset = pd.DataFrame([{'question':'1+1?',  'answer': 2,'score':1.0, 'categories':[{'index':0,'score':1},{'index':1,'score':1.0},{'index':2,'score':0.0}]},
			    {'question':'20+20?','answer':40,'score':1.0, 'categories':[{'index':0,'score':1},{'index':1,'score':0.0},{'index':2,'score':1.0}]},
			    {'question':'2+2?',  'answer': 5,'score':0.0, 'categories':[{'index':0,'score':1},{'index':1,'score':1.0},{'index':2,'score':0.0}]}])
    categories = pd.DataFrame([{'title':'everything', 'description':'The entire dataset'},
                               {'title':'Single digit addition','description':'Math problems that involve only adding single digit numbers together'},
                               {'title':'Two digit addition','description':'Math problems that involve only adding two digit numbers together'}])
    score_categories(dataset, categories, data_cat_col='categories', data_metric_col='score', cat_score_col='score')
    print(categories.to_csv(sep='\t'))
	title			description								score n_covered	f_covered
0	everything		The entire dataset							0.66	3	1.0
1	Single digit addition	Math problems that involve only adding single digit numbers together	0.5	2	0.66
2	Two digit addition	Math problems that involve only adding two digit numbers together	1.0	1	0.33
"""
def score_categories(dataset:pd.DataFrame, categories:pd.DataFrame, *, data_cat_col:str, data_metric_col:str, cat_score_col:str):
    overall_n_covered = len(dataset)

    for index, category_row in categories.iterrows():
        category_scores = []
        for _, row in dataset.iterrows():
            for category in row[data_cat_col]:
                if category['index'] == index and category['score'] > 0.5:
                    category_scores.append(row[data_metric_col])

#       average_score = sum(category_scores) / len(category_scores) if category_scores else '?'        	# '?' leads to a dtype warning
        average_score = sum(category_scores) / len(category_scores) if category_scores else 0
        categories.at[index, cat_score_col] = average_score
        categories.at[index, 'n_covered'] = int(len(category_scores))
#       print(categories.at[category_row.name, 'n_covered'])		# for unknown reasons, the cell is still a float

        categories.at[category_row.name, 'f_covered'] = len(category_scores) / overall_n_covered        

    categories['n_covered'] =  categories['n_covered'].astype(int)		# for some reason they are floats
    return categories

### ----------------------------------------

"""
U: Now add a 'Adjusted Score' computed from the 'Score' via the following formula:

    adjusted_score_basis = 10
    adjusted_score = ((score*n_covered) + 1) / (n_covered + adjusted_score_basis)

Now add another column to question_categories containing the absolute difference between the 'Adjusted Score' and the overall average score, contained in the 'Score' of row 0 of question_categories.
"""
ADJUSTED_SCORE_BASIS = 10

def add_signal(categories, score_col:str, adj_score_col:str, signal_col:str, adj_signal_col:str):
    """Adds columns 'signal' and 'adjusted_signal' to the categories DataFrame.
    Args:
    categories: A DataFrame containing categories and their scores.
    Returns:
    The modified DataFrame.
    """
    overall_average_score = categories.loc[0, score_col]		# index 0 is "everything"

    def calculate_signal_and_adjusted_signal(row):
        score = row[score_col]
        n_covered = row['n_covered']

        if score == '?':
            return '?', 0, 0
        else:
            signal = abs(score - overall_average_score)		# overall_average_score is global to add_signal's scope
            adjusted_score = ((score * n_covered) + (overall_average_score * ADJUSTED_SCORE_BASIS)) / (n_covered + ADJUSTED_SCORE_BASIS)
            adjusted_signal = abs(adjusted_score - overall_average_score)
            return adjusted_score, signal, adjusted_signal

    categories[[adj_score_col, signal_col, adj_signal_col]] = categories.apply(calculate_signal_and_adjusted_signal, axis=1, result_type='expand')

    return categories  



