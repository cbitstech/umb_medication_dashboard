from django.http import HttpResponse
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
import json
from umb_dashboard.views import respond_with_json
from umb_dashboard.models import MedPromptResponse, SentMessage
from heart2haart.models import SideEffectsSurveyResponse, \
  MoodSurveyResponse, CravingsSurveyResponse, ClinicianAlert, Participant, \
  ParticipantAction

@login_required
def participants(request):
  return respond_with_json(Participant.objects.all())

@login_required
#@cache_page()
def side_effects_survey_responses(request, participant_id):
  responses = SideEffectsSurveyResponse.objects.all_for_participant(participant_id)
  return respond_with_json(responses)

@login_required
#@cache_page()
def mood_survey_responses(request, participant_id):
  responses = MoodSurveyResponse.objects.all_for_participant(participant_id)
  return respond_with_json(responses)

@login_required
#@cache_page()
def cravings_survey_responses(request, participant_id):
  responses = CravingsSurveyResponse.objects.all_for_participant(participant_id)
  return respond_with_json(responses)

@login_required
def update_clinician_alert(request, participant_id, alert_id):
  from django.core import serializers
  for alert in serializers.deserialize("json", request.body):
    alert.save()
  return HttpResponse()

@login_required
def uncleared_clinician_alerts(request, participant_id):
  alerts = []
  alert_types = ["non_adherence", "side_effects", "mood", "cravings"]
  for alert_type in alert_types:
    alert = find_uncleared_alert(participant_id, alert_type)
    if alert != None:
      alerts.append(alert)
  return respond_with_json(alerts)

def find_uncleared_alert(participant_id, alert_type):
  import datetime
  alert_manager = ClinicianAlert.objects
  alerts = alert_manager.filter(participant_id=participant_id, type=alert_type, is_cleared=False) or []
  if len(alerts) == 0:
    last_cleared_alerts = alert_manager.filter(participant_id=participant_id, type=alert_type, is_cleared=True).order_by('-created_at')[:1]
    last_alert_timestamp = datetime.datetime.min
    if len(last_cleared_alerts) == 1:
      last_alert_timestamp = last_cleared_alerts[0].updated_at
    details = pending_alert_details(last_alert_timestamp, participant_id, alert_type)
    if len(details) > 0:
      participant_requests_contact = any_contact_requests(last_alert_timestamp, participant_id, alert_type)
      alert = alert_manager.create(participant_id=participant_id, type=alert_type,
        problem_details=details, participant_requests_contact=participant_requests_contact)
      alerts.append(alert)
  if len(alerts) == 1:
    return alerts[0]
  return None

def pending_alert_details(last_alert_timestamp, participant_id, alert_type):
  if alert_type == "non_adherence":
    return pending_negative_med_prompt_responses(last_alert_timestamp, participant_id)
  elif alert_type == "side_effects":
    return pending_negative_side_effects_responses(last_alert_timestamp, participant_id)
  elif alert_type == "mood":
    return pending_negative_mood_responses(last_alert_timestamp, participant_id)
  elif alert_type == "cravings":
    return pending_negative_cravings_responses(last_alert_timestamp, participant_id)

def pending_negative_med_prompt_responses(last_alert_timestamp, participant_id):
  responses = MedPromptResponse.objects.negative_responses(participant_id, start_time=last_alert_timestamp)
  details = (r.doseTime for r in responses)

  return filter(None, details)

def pending_negative_side_effects_responses(last_alert_timestamp, participant_id):
  HIGH_FREQ = 'Always'
  responses = SideEffectsSurveyResponse.objects.negative_responses(participant_id, last_alert_timestamp)
  details = []
  details.append(next(("index" for r in responses if r.weight_concern_distress == HIGH_FREQ), None))
  details.append(next(("sexual_problems" for r in responses if r.sexual_problems_distress == HIGH_FREQ), None))
  details.append(next(("insomnia" for r in responses if r.insomnia_distress == HIGH_FREQ), None))
  details.append(next(("restlessness" for r in responses if r.restlessness_distress == HIGH_FREQ), None))
  details.append(next(("low_energy" for r in responses if r.low_energy_distress == HIGH_FREQ), None))
  details.append(next(("not_like_self" for r in responses if r.not_like_self_distress == HIGH_FREQ), None))
  details.append(next(("excess_sedation" for r in responses if r.excess_sedation_distress == HIGH_FREQ), None))
  details.append(next(("poor_concentration" for r in responses if r.poor_concentration_distress == HIGH_FREQ), None))
  details.append(next(("trembling" for r in responses if r.trembling_distress == HIGH_FREQ), None))

  return filter(None, details)

def pending_negative_mood_responses(last_alert_timestamp, participant_id):
  HIGH_FREQ = 'Almost all of the time'
  responses = MoodSurveyResponse.objects.negative_responses(participant_id, last_alert_timestamp)
  details = []
  details.append(next(("index" for r in responses if r.paranoia_frequency == HIGH_FREQ), None))
  details.append(next(("media_communication" for r in responses if r.media_communication_frequency == HIGH_FREQ), None))
  details.append(next(("thought_insertion" for r in responses if r.thought_insertion_frequency == HIGH_FREQ), None))
  details.append(next(("special_mission" for r in responses if r.special_mission_frequency == HIGH_FREQ), None))
  details.append(next(("thought_broadcasting" for r in responses if r.thought_broadcasting_frequency == HIGH_FREQ), None))
  details.append(next(("hallucinations" for r in responses if r.hallucinations_frequency == HIGH_FREQ), None))
  details.append(next(("confused" for r in responses if r.confused_frequency == HIGH_FREQ), None))
  details.append(next(("thought_disorders" for r in responses if r.thought_disorders_frequency == HIGH_FREQ), None))

  return filter(None, details)

def pending_negative_cravings_responses(last_alert_timestamp, participant_id):
  HIGH_FREQ = 'Almost all of the time'
  responses = CravingsSurveyResponse.objects.negative_responses(participant_id, last_alert_timestamp)
  details = []
  details.append(next(("index" for r in responses if r.paranoia_frequency == HIGH_FREQ), None))
  details.append(next(("media_communication" for r in responses if r.media_communication_frequency == HIGH_FREQ), None))
  details.append(next(("thought_insertion" for r in responses if r.thought_insertion_frequency == HIGH_FREQ), None))
  details.append(next(("special_mission" for r in responses if r.special_mission_frequency == HIGH_FREQ), None))
  details.append(next(("thought_broadcasting" for r in responses if r.thought_broadcasting_frequency == HIGH_FREQ), None))
  details.append(next(("hallucinations" for r in responses if r.hallucinations_frequency == HIGH_FREQ), None))
  details.append(next(("confused" for r in responses if r.confused_frequency == HIGH_FREQ), None))
  details.append(next(("thought_disorders" for r in responses if r.thought_disorders_frequency == HIGH_FREQ), None))

  return filter(None, details)

def any_contact_requests(last_alert_timestamp, participant_id, alert_type):
  messages = SentMessage.objects.all_in_context(participant_id, alert_type, last_alert_timestamp)

  return len(messages) > 0

@login_required
#@cache_page()
def latest_action(request, participant_id):
  return respond_with_json(ParticipantAction.objects.latest(participant_id))