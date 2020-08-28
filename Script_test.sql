select o.data as date, o.AO, o.result, COUNT(o.AO), SUM(o.audio_length), p.name as project_name, p.description as project_description, s.name as name_server, s.ip_address as server_ip_address, s.description as server_description
from speech_to_text.operations as o
JOIN speech_to_text.project as p ON p.id = o.projectid
JOIN speech_to_text.server as s ON s.id = o.serverid 
where data<'2020-08-30' and data>'2020-08-27'
group by data, AO, result, p.name, p.description, s.name, s.ip_address, s.description
order by data;