from login_gmail_selenium.util.profiles.profile import GoogleProfile
from login_gmail_selenium.util.profiles.google_profile import Profile

profile = GoogleProfile(email, password, backup_email)
# profile = Profile(name_profile) If don't need login to google but save driver
# To allow downloads add insecure=True to ChromeProfile
# To handle false email with custom functions, use param false_email_callback
driver = profile.retrieve_driver()
profile.start()
# Do whatever with driver afterward
driver.get('https://www.google.com/')
driver.quit()
# instalation: pip install login_gmail_selenium