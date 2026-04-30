class AppointmentManager:
    def __init__(self):
        self.appointments = []

    def add_appointment(self, date_time, patient_name, doctor_name):
        appointment = {
            'date_time': date_time,
            'patient_name': patient_name,
            'doctor_name': doctor_name
        }
        self.appointments.append(appointment)
        print(f"Added appointment for {patient_name} with {doctor_name} on {date_time}")

    def get_appointments(self):
        return self.appointments

    def find_appointment(self, patient_name):
        return [appt for appt in self.appointments if appt['patient_name'] == patient_name]

    def remove_appointment(self, date_time, patient_name):
        self.appointments = [appt for appt in self.appointments if not (appt['date_time'] == date_time and appt['patient_name'] == patient_name)]
        print(f"Removed appointment for {patient_name} on {date_time}")

# Example Usage
if __name__ == '__main__':
    manager = AppointmentManager()
    manager.add_appointment('2023-05-01 15:00:00', 'John Doe', 'Dr. Smith')
    print(manager.get_appointments())