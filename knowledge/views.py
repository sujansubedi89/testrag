from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
import os

# Create your views here.
from .models import Document, ChatSession, Message
from .serializers import DocumentSerializer, ChatSessionSerializer
from .rag import ingest_document, ask_question
from django.shortcuts import render

def index(request):
    return render(request, 'knowledge/index.html')

class DocumentUploadView(APIView):
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': 'No file provided'}, status=400)

        doc = Document.objects.create(
            file=file,
            name=file.name,
            status='processing'
        )

        try:
            file_path = os.path.join(settings.MEDIA_ROOT, doc.file.name)
            ingest_document(file_path, doc.id)
            doc.status = 'done'
            doc.save()
        except Exception as e:
            doc.status = 'failed'
            doc.save()
            return Response({'error': str(e)}, status=500)

        return Response(DocumentSerializer(doc).data, status=201)


class ChatView(APIView):
    def post(self, request):
        question = request.data.get('question')
        doc_id = request.data.get('doc_id')
        session_id = request.data.get('session_id', None)

        if not question or not doc_id:
            return Response({'error': 'question and doc_id are required'}, status=400)

        try:
            doc = Document.objects.get(id=doc_id, status='done')
        except Document.DoesNotExist:
            return Response({'error': 'Document not found or not ready'}, status=404)

        # Get or create session
        if session_id:
            session, _ = ChatSession.objects.get_or_create(id=session_id, document=doc)
        else:
            session = ChatSession.objects.create(document=doc)

        answer = ask_question(question, doc.id)

        Message.objects.create(session=session, question=question, answer=answer)

        return Response({
            'session_id': session.id,
            'question': question,
            'answer': answer
        })