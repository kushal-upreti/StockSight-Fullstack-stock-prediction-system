from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Bookmark
from .serializers import BookmarkSerializer

class BookmarkListView(APIView):
    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user)
        serializer = BookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = BookmarkSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BookmarkDetailView(APIView):
    def get_object(self, pk, user):
        try:
            return Bookmark.objects.get(pk=pk, user=user)
        except Bookmark.DoesNotExist:
            return None

    def get(self, request, pk):
        bookmark = self.get_object(pk, request.user)
        if not bookmark:
            return Response({'error': 'Bookmark not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookmarkSerializer(bookmark)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        bookmark = self.get_object(pk, request.user)
        if not bookmark:
            return Response({'error': 'Bookmark not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = BookmarkSerializer(bookmark, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        bookmark = self.get_object(pk, request.user)
        if not bookmark:
            return Response({'error': 'Bookmark not found.'}, status=status.HTTP_404_NOT_FOUND)
        bookmark.delete()
        return Response({'message': 'Bookmark deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)