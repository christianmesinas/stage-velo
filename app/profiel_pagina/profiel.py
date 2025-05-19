from behave import given, when, then
from assertpy import assert_that

#profiel bekijken als ingelogde gebruiker
@given("de gebruiker is ingelogd")
def step_impl(context):
    context.user = {
        "is_authenticated": True,
        "name": "Jan Jansen",
        "email": "jan@example.com",
        "payment_method": "Visa",
        "subscription": "Premium",
        "ride_history": ["Rit 1", "Rit 2"]
    }

@when("de gebruiker navigeert naar zijn profielpagina")
def step_impl(context):
    if context.user["is_authenticated"]:
        context.profile_data = context.user
    else:
        context.profile_data = None

@then("ziet de gebruiker zijn naam, e-mailadres, gekoppelde betaalmethode, abonnementstype en ritgeschiedenis")
def step_impl(context):
    assert_that(context.profile_data).is_not_none()
    assert_that(context.profile_data).contains_key(
        "name", "email", "payment_method", "subscription", "ride_history"
    )

#Profiel proberen te bekijken zonder ingelogd te zijn
@given("de gebruiker is niet ingelogd")
def step_impl(context):
    context.user = {
        "is_authenticated": False
    }

@when("de gebruiker probeert zijn profielpagina te openen")
def step_impl(context):
    if not context.user["is_authenticated"]:
        context.error_message = "Je moet eerst inloggen"
    else:
        context.error_message = None

@then("krijgt de gebruiker een melding dat hij eerst moet inloggen")
def step_impl(context):
    assert_that(context.error_message).is_equal_to("Je moet eerst inloggen")

#Navigeren vanuit profiel naar instellingen
@given("de gebruiker bekijkt zijn profielpagina")
def step_impl(context):
    context.current_page = "profiel"

@when('de gebruiker klikt op "Instellingen"')
def step_impl(context):
    if context.current_page == "profiel":
        context.current_page = "instellingen"

@then("wordt de gebruiker doorgestuurd naar de instellingenpagina")
def step_impl(context):
    assert context.current_page == "instellingen"