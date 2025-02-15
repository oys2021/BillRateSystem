from django.db import models

class Project(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class Timesheet(models.Model):
    employee_id = models.IntegerField()
    billable_rate = models.DecimalField(max_digits=10, decimal_places=2)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    sheet_name = models.CharField(max_length=255)  
    created_at=models.DateTimeField(auto_now_add=True)
    

    class Meta:
        unique_together = ('employee_id', 'project', 'date', 'start_time', 'end_time')
        
    def __str__(self):
        return f"{self.sheet_name}--{self.created_at}"
    

 
