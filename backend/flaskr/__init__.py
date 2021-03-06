import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category


QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    app = Flask(__name__)
    setup_db(app)
    cors = CORS(
        app, resources={r"/api/*": {
            "origins": "*"}}, supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers',
            'Content-Type, Authorization, true')
        response.headers.add(
            'Access-Control-Allow-Methods',
            'GET, POST, PATCH, DELETE, OPTIONS')
        return response

    @app.route('/')
    def index():
        return 'Welcome to Trivia API'

    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        categories_list = {}
        for category in categories:
            categories_list[category.id] = category.type

        return jsonify({
            'success': True,
            'categories': categories_list
            })

    @app.route('/categories/<int:category_id>')
    def get_specific_category(category_id):
        category = Category.query.filter(
            Category.id == category_id).one_or_none()

        if category is None:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'category': category.format()
            })

    @app.route('/questions', methods=['GET'])
    def get_questions():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        categories = list(map(Category.format, Category.query.all()))

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories,
            'current_category': None
        })

    @app.route('/questions/<int:question_id>')
    def get_specific_question(question_id):
        question = Question.query.filter(
            Question.id == question_id).one_or_none()

        if question is None:
            abort(404)

        else:
            return jsonify({
                'success': True,
                'question': question.format()
            })

    @app.route('/questions/<int:question_id>', methods=['GET', 'DELETE'])
    def delete_questions(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
                abort(422)

    @app.route('/questions/add', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', None)
        new_category = body.get('category', None)

        try:
            question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)

            question.insert()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        search = body.get('searchTerm', None)

        try:
            selection = Question.query.order_by(Question.id).filter(Question.question.ilike('%{}%'.format(search))).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'questions': current_questions,
                'total_questions': len(current_questions)
            })

        except:
            abort(422)
    
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def questions_by_category(category_id):
        try:
            category_id = int(category_id)
            selection = Question.query.filter(
                Question.category == category_id).all()
            current_questions = paginate_questions(request, selection)
            
            if len(selection) == 0:
                abort(404)
            else:
                return jsonify({
                    'questions': current_questions,
                    'total_questions': len(Question.query.all()),
                    'current_category': category_id
                })
        except:
            abort(422)

    @app.route('/questions/<int:question_id>', methods=['GET', 'PATCH'])
    def update_question(question_id):
        body = request.get_json()

        try:

            question = Question.query.filter(
                Question.id == question_id).one_or_none()

            if question is None:
                abort(404)

            if 'question' in body:
                question.question = str(body.get('question'))
            if 'answer' in body:
                question.answer = str(body.get('answer'))
            if 'category' in body:
                question.category = str(body.get('category'))
            if 'difficulty' in body:
                question.difficulty = str(body.get('difficulty'))

            question.update()

            return jsonify({
                'success': True,
                'id': question.id
            })

        except:
            abort(404)

    @app.route('/play', methods=['GET', 'POST'])
    def receive_quiz_questions():
        body = request.get_json()
        former_questions = body.get('previous_questions', [])
        category_quiz = body.get('quiz_category', None)

        try:
            
            if category_quiz['id'] == 0:
                quiz_questions = Question.query.all()
            else:
                quiz_questions = Question.query.filter_by(category=category_quiz['id']).all()

            selection = []
            for question in quiz_questions:
                if question.id not in former_questions:
                    selection.append(question.format())
            if len(selection) != 0:
                result = random.choice(selection)
                return jsonify({
                    'question': result
                })
            else:
                return jsonify({
                    'question': False
                })
        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Resource not found.'
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'Unprocessable.'
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad request.'
        }), 400

    @app.errorhandler(405)
    def no_valid_method(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method not allowed.'
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal Server Error'
        }), 500

    return app
