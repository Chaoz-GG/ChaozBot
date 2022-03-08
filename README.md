For auto-start, run the below commands *from the user account in which the bot exists*:

```shell
crontab -l | { cat; echo "@reboot sleep 60 && screen -S ChaozBot /home/chaozbot/ChaozBot/monitor"; } | crontab -
crontab -l | { cat; echo "@reboot sleep 60 && screen -S ChaozBot /home/chaozbot/StatsAPI/monitor"; } | crontab -
```