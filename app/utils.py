from flask import redirect, url_for, flash
import os
import smtplib
from openai import OpenAI
import ast
from .models import Workout, Exercises, WorkoutExercises, db
import random


def send_mail(name, email, phone, message):
    gmail_user = os.getenv('GMAIL_USERNAME')
    gmail_password = os.getenv('GMAIL_PASSWORD')

    sent_from = gmail_user
    to = [gmail_user]
    subject = f'Message from: Name- {name} Email- {email}, Phone- {phone}'

    email_text = f"""From: {sent_from}\nTo: {", ".join(to)}\nSubject: {subject}\n\n{message}"""

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_user, gmail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()
        flash("Thanks for reaching us. Your message has been sent!")
        return 'Success'

    except Exception as e:
        flash(f'Something went wrong. Message not send.')
        print(e)
        return 'Failure'


def generate_ai_workout(duration, fitness_level, fitness_goal, equipment_access, running_type):
    api_key = os.getenv('OPENAI_API_KEY')
    client = OpenAI(api_key=api_key)

    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": (
                    f"Create a workout plan with only the workout name and details based on these criteria:\n"
                    f"- Workout Duration: '{duration} minutes'\n- Fitness Level: '{fitness_level}'\n- "
                    f"Fitness Goal: '{fitness_goal}'\n- Equipment Access: '{equipment_access}'\n- Running Type: '{running_type}'\n\n"
                    "Format:\n{\n  'workout_name': 'Name of the workout',\n  "
                    "'workout_details': [('Exercise Name', 'Description', Sets, Repetitions, 'Rest Time in minutes'), ...]\n}\n"
                    "Note: Provide the response in this exact format, without any additional text.\n"
                    "Provide a workout name that reflects the workout's focus and goal, e.g., 'Intense Cardio Circuit' or 'Beginners Full-Body Strength. with no punctuation marks"
                )
            }
        ]
    )

    workout_output = completion.choices[0].message.content
    workout_output = workout_output.replace("'", '"')

    return ast.literal_eval(workout_output)


def get_number_of_workouts():
    return db.session.query(Workout).count() // 10 * 10


def get_number_of_exercises():
    return db.session.query(Exercises).count() // 10 * 10


def get_workout_from_db(workout_type, duration, fitness_level, fitness_goal=None, equipment_access=None,
                        running_type=None):
    workouts = Workout.query.filter(
        Workout.workout_type == workout_type,
        Workout.workout_duration == duration,
        Workout.fitness_level == fitness_level,
        Workout.fitness_goal == fitness_goal,
        Workout.equipment_access == equipment_access,
        Workout.running_type == running_type
    ).all()

    print(workouts)
    print(workout_type, duration, fitness_level, fitness_goal, equipment_access, running_type)
    return workouts


def get_workout_id(workouts):
    workout_ids = [workout.workout_id for workout in workouts]
    selected_workout_id = random.choice(workout_ids)
    return selected_workout_id


def get_workout_by_id(workout_id):
    workout_details = db.session.query(
        Workout.workout_name,
        Exercises.exercise_name,
        Exercises.exercise_description,
        WorkoutExercises.sets,
        WorkoutExercises.repetitions,
        WorkoutExercises.rest_time
    ).join(WorkoutExercises, WorkoutExercises.exercise_id == Exercises.exercise_id) \
        .join(Workout, Workout.workout_id == WorkoutExercises.workout_id) \
        .filter(Workout.workout_id == workout_id) \
        .all()
    return workout_details