import requests
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .serializers import StockPredictionSerializer
from datetime import datetime
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, r2_score
from .stock_models.ml_models import get_model

model = get_model()
# Create your views here.

class StockPredictionAPIView(APIView):
    def post(self, request):
        serializer = StockPredictionSerializer(data = request.data)
        if serializer.is_valid():
            ticker = serializer.validated_data['ticker']
            days = serializer.validated_data['days']
            
            df = yf.download(ticker, period='10y', auto_adjust=False)
            if df.empty:
                return Response(
                    {
                        'error': 'No data found for the given ticker',
                        'status': status.HTTP_404_NOT_FOUND
                    }
                )
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)  # flatten to single level

            df= df.reset_index()

            # Splitting data into Training & Testing datasets
            data_training = pd.DataFrame(df.Close[0:int(len(df)*0.7)])
            data_testing = pd.DataFrame(df.Close[int(len(df)*0.7):int(len(df))])

            # Scaling down the data between 0 and 1
            scaler = MinMaxScaler(feature_range=(0,1))
            


            past_100_days = data_training.tail(100)
            final_df = pd.concat([past_100_days, data_testing], ignore_index=True)
            input_data = scaler.fit_transform(final_df)

            x_test = []
            y_test = []
            for i in range(100, input_data.shape[0]):
                x_test.append(input_data[i-100: i])
                y_test.append(input_data[i, 0])
            x_test, y_test = np.array(x_test), np.array(y_test)

             # Making Predictions
            current_value=[]
            prediction_result= []
            y_predicted = model.predict(x_test)

            # Revert the scaled prices to original price
            prediction_result = scaler.inverse_transform(y_predicted.reshape(-1, 1)).flatten().tolist()

            current_value = scaler.inverse_transform(y_test.reshape(-1, 1)).flatten().tolist()

            # Model Evaluation
            # Mean Squared Error (MSE)
            mse = mean_squared_error(current_value, prediction_result)

            # Root Mean Squared Error (RMSE)
            rmse = np.sqrt(mse)

            # R-Squared
            r2 = r2_score(current_value, prediction_result)

            # recent_prices = [
            #     {'date': str(row['Date'])[:10], 'close': float(row['Close'])}
            #     for _, row in df.iterrows()
            #     ]

            return Response({
                'status': 'success',
                'mse': float(mse),
                'rmse': float(rmse),
                'r2': float(r2),
                'predict_value':prediction_result,
                'current_value':current_value,
                # 'recent_prices': recent_prices,
                })
        
        return Response({
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
# <-----------------------------------------------------------------------------------------------------> 
        # # N-days prediction code
        #     # past_100_days_stock_data = df[['Close']].tail(100)
           
        #     # shaping data into 2D array

        #     #scaling the data
        #     # scaler = MinMaxScaler(feature_range=(0,1))
        #     scaled_data = scaler.fit_transform(past_100_days)

        #     final_data_for_prediction= np.reshape(scaled_data, (1, 100, 1))

        #     predictions = []
        #     for _ in range(days):

        #         next_pred = model.predict(final_data_for_prediction)
        #         predictions.append(float(next_pred[0,0]))

        #         next_pred_reshaped = next_pred.reshape(1,1,1)

        #         final_data_for_prediction = np.concatenate(
        #             (final_data_for_prediction[:,1:,:], next_pred_reshaped),
        #             axis=1
        #         )
        #     predictions = np.array(predictions).reshape(-1,1)
        #     predicted_data_non_scaled= scaler.inverse_transform(predictions).flatten()

        #     return Response(
        #         {
        #             'status':'success',
        #             'predict_value':predicted_data_non_scaled.tolist()
        #         }, status= status.HTTP_200_OK)
        
        # return Response({
        #     "errors": serializer.errors
        # }, status=status.HTTP_400_BAD_REQUEST)


class TickerInfoAPIView(APIView):

     def get(self, request):
        ticker = request.query_params.get('ticker')
        if not ticker:
            return Response({'error': 'Ticker is required'}, status= status.HTTP_400_BAD_REQUEST)
        
        try:
            info= yf.Ticker(ticker).info
            return Response({
                'Symbol': info.get('symbol', ticker),
                'Name': info.get('longName', '---'),
                'Industry': info.get('industry', '---'),
                'Country': info.get('country', '---'),
                'Exchange': info.get('exchange', '---'),
                'Currency': info.get('currency', '---'),
                'Market Cap': info.get('marketCap', '---'),
                'Website': info.get('website', '---'),
                'Description': info.get('longBusinessSummary', '---')
            })
        except Exception as e:
            return Response({'error': str(e)}, status= status.HTTP_500_INTERNAL_SERVER_ERROR)