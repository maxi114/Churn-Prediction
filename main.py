from sys import exec_prefix
import streamlit as st
import pandas as pd
import pickle
import numpy as np
import os
from openai import OpenAI

#open AI api key
client = OpenAI(
  base_url ="https://api.groq.com/openai/v1",
  api_key = os.environ['GROQ_API_KEY']
)


def load_model(filename):
  with open(filename, "rb") as file:
    return pickle.load(file)

xgboost_model = load_model('Xgb_model.pkl')

naive_bayes_model = load_model('nb_model.pkl')

random_forest_model = load_model('rf_model.pkl')

decision_tree_model = load_model('dt_model.pkl')

svm_model = load_model('svm_model.pkl')

knn_model =  load_model('knn_model.pkl')

voting_classifier_model = load_model('voting_clf.pkl')

xgboost_SMOTE_model = load_model('xgboost-SMOTE.pkl')

xgboost_featureEngineered_model = load_model("xgboost-featureEngineered.pkl")


def prepare_input(credit_score, location, gender, age, tenure, balance, 
                 num_products, has_credit_card, is_active_member, estimated_salary):

  input_dict = {
    'CreditScore': credit_score,
    'Age': age,
    'Tenure': tenure,
    "Balance": balance,
    "NumOfProducts": num_products,
    'HasCard': int(has_credit_card),
    'IsActiveMember': int(is_active_member),
    "EstimatedSalary": estimated_salary,
    "Geograpgy_France" : 1 if location == "France" else 0,
    "Geograpgy_Germany": 1 if location == "Germany" else 0,
    "Geograpgy_Spain": 1 if location == "Spain" else 0,
    "Gender Male": 1 if gender == "Male" else 0,
    "Gender Female": 1 if gender == "Female" else 0,
  }

  input_df = pd.DataFrame([input_dict])
  return input_df, input_dict

def make_prediction(input_df, input_dict):

  probabilities = {
    'XGBoost': xgboost_model.predict_proba(input_df)[0][1],
    "Random Foresy": random_forest_model.predict_proba(input_df)[0][1],
    'K-Nearest Neighbors': knn_model.predict_proba(input_df)[0][1],
  }

  avg_probability = np.mean(list(probabilities.values()))

  st.markdown("### Model Probabilities")
  for model, prob in probabilities.items():
    st.write(f'{model} {prob}')
  st.write(f"Average Probability: {avg_probability}")

  return avg_probability



def explain_prediction(probability, input_dict, surname):

  prompt = f"""You are an expert data scientist at a bank, where you specialize in interpreting and explaining prediction of machine learning models.
  
  Your machine learning model has predicted that a customer named {surname} has a {round(probability * 100, 1)}% probability of churning, based on the infromation provided below.
  
  Here is the customer's information:
  {input_dict}
  
  Here are the machine learning model's top 10 most important features for predicting churn:
  
                          Feature | importance
                        ------------------------------
                        NumOfProducts  |  0.32888
                        IsActiveMember |  0.164146
                                  Age  |  0.109550
                      Geography_Germany|  0.091373
                              Balance  |  0.052786
                       Geography_France|  0.046463
                       Gender_Female   |  0.045283
                       Geography_Spain |  0.036855
                       CreditSocre     |  0.035005
                       EstimatedSalary |  0.032655
                       HasCrCard       |  0.031940
                       Tenure          |  0.030054
                       Gender_Male     |  0.000000
                       
                       {pd.set_option('display.max_columns', None)}
                       
                       Here are summary statistics for churned customers:
                       {df[df['Exited'] == 1].describe()}
                       
                       - if the customer has over a 40% risk of churning, generate a 3 sentence explanation of why they are at risk of churning.
                       -If the customer has less than a 40% rsk of churning, generate a 3 sentence explanation of why they might not be at risk of chuning.
                       -your explanation should be based on he customer's information, the statistics  of churned and non-churned customers, and the feature importances provided.
                       
                       Don't mention the probability of churning, or the machine learning model, or say anything like "Based on the machine learning model's prediction and top 10 most important features", just explain the prediction
                       """

  print("EXPLANATION PROMPT", prompt)
  
  raw_response = client.chat.completions.create(
    model = 'llama-3.1-8b-instant',
    messages = [{
      "role" : "user",
      "content": prompt
  
    }],
  )

  return raw_response.choices[0].message.content

st.title("Customer Churn Prediction")

df =pd.read_csv("churn.csv")

customers = [f"{row['CustomerId']} - {row['Surname']}" for _, row in df.iterrows()]

selected_customer_option = st.selectbox("select a customer", customers)

if selected_customer_option:

  selected_customer_id = int(selected_customer_option.split(" - ")[0])
  print("Selected Customer ID", selected_customer_id)

  selected_surname = selected_customer_option.split(" - ")[1]

  print("Surname", selected_surname)

  selected_customer = df.loc[df['CustomerId'] == selected_customer_id].iloc[0]

  print("Selected Customer", selected_customer)

  col1, col2 = st.columns(2)

  with col1:

    credit_score = st.number_input(
      "Credit score",
      min_value = 300,
      max_value = 850,
      value=int(selected_customer['CreditScore']))

    location = st.selectbox(
      "Location",["Spain", "France", "Germany"],
      index=["Spain","France","Germany"].index(
        selected_customer["Geography"]))
  
    gender = st.radio("Gender", ["Male", "Female"],
                    index = 0 if selected_customer['Gender'] == "Male" else 1)
  
    age = st.number_input(
      "Age",
      min_value = 18,
      max_value = 100,
      value = int(selected_customer['Age'])
    )
  
    tenure = st.number_input(
      "Tenure (years",
      min_value = 0,
      max_value=50,
      value=int(selected_customer['Tenure']))

  with col2:

    balance = st.number_input(
      "Balance",
      min_value = 0.0,
      value = float(selected_customer['Balance']))

    num_products = st.number_input(
      "Number of Products",
      min_value = 1,
      max_value = 10,
      value = int(selected_customer['NumOfProducts']))

    has_credit_card = st.checkbox(
      "Has Credit Card",
      value = bool(selected_customer['HasCrCard']))

    is_active_member = st.checkbox(
      "Is Active Member",
      value=bool(selected_customer['IsActiveMember']))

    estimated_salary = st.number_input(
      "Estimated Salary",
      min_value=0.0,
      value=float(selected_customer['EstimatedSalary'])
    )

  input_df, input_dict = prepare_input(credit_score, location, gender, age, tenure, balance, 
       num_products, has_credit_card, is_active_member, estimated_salary)
  
  avg_probability = make_prediction(input_df, input_dict)

  explanation = explain_prediction(avg_probability, input_dict, selected_customer['Surname'])

  st.markdown("---")
  
  st.subheader("Explanation of Prediction")
  
  st.markdown(explanation)
  