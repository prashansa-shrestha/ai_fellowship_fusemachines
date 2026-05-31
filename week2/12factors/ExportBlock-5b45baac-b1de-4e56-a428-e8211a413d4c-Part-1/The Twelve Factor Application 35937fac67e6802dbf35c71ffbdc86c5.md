# The Twelve Factor Application

Think of Starlink. It is an internet service available almost anywhere on the earth, from the top of the Sagarmatha (Mt. Everest) to the Amazon rainforest in Brazil. It can easily provide services to a single explorer in the jungle as well as 10,000 users in the city.

Any modern application that we use day to day (think YouTube, and HamroPatro) needs to be similarly portable, scalable (can be used by 1-100000.. users), and operable across any environment (you wouldn’t want to go to your aunt’s house only to find out YouTube doesn’t work there, right?).

The 12-factor app is a methodology for building SaaS (Software as a Service) applications that are portable, scalable, and resilient when deployed to the web. It was proposed by engineers working at [Heroku](https://www.heroku.com/)

You can look into the original documentation here: 

https://12factor.net/

This  YouTube video is really good as well:

https://www.youtube.com/watch?v=1OhmRmMsGdQ

# The Twelve Factors

## Codebase

*You use a single code repository from which you make multiple deployments.*

<aside>
💡

For newbies:

- a repository is simply a digital storage location where all the files, folders, and data for a project is kept.
- a deployment is your codebase running
</aside>

- Each app has only a single codebase, which will be deployed multiple times over it’s period.
Eg. Facebook has one codebase, but it is **deployed multiple times** simultaneously: once to the 'Production' environment for billions of users, and once to a 'Staging' environment where developers test new features before they go live.
- If a system has multiple codebases, then it is not an app. It’s a distributed system, and each component from the codebase is an app.
Eg. Your TV’s code is one app; your TV remote’s function is another. They are two separate codebases that talk to each other to form a "System.”
- Multiple applications cannot share the same codebase. Such requirement is fulfilled by factoring the required shared code into libraries that you can import (at the top of your code file).
Eg. your "Pathao Rider" app and "Pathao User" app need to show the exact same logo and brand colors, you don't copy-paste the code. You put those styles into a **UI Library**. Both apps then "import" that library.

## Dependencies

*All dependencies that your app uses must be explicitly declared, and your app must run inside a protected bubble, so that it is unaffected by the status of your local machine.*

<aside>
💡

dependency: any external code or software that your application depends on to function properly

</aside>

- A twelve factor app never assumes that the computer it’s running on already has the tools it needs. It carries its own instructions for everything.
- Your app should only require a single command for a new developer to get it working.
This means no manual installation of software or version errors.
Eg. running pip install -r requirements.txt should be enough to get your app running
    
    (I’m a slytherin girl)
    
- Your app should not rely on tools that are installed in your computer (eg. curl, grep, git). It should bring its own tools by including them as internal libraries.
    
    Eg. your plumber arrives at your home to fix your shower without her toolbox, because she assumes “you have one already, because everyone does”
    
- Next, we have the “roommate problem”. Two people live in the same room, but one needs the thermostat at 20 degrees celsius, and the other needs it at 25.
    
    Isolation ensure both get their desired temperature inside the same room.
    
    Your calculator app runs on Python 2.7 and your custom DeepSeek LLM runs on Python 3.11. To fulfill both their requirements, you give each one a private copy of it’s library using a tool like Docker, or virtual environment. With this, each app gets its own toolbox, without getting affected by whatever another app on the computer uses.
    

## Config

*store configuration in the environment, not in the code or config files*

Config (short for configuration) is the collection of settings and secrets that your code uses. Examples: API keys, your passwords etc. It differs in each usage, so it is kept separate from the code, so that the code itself never has to change when you move it from your computer to a live server.

### **How do I know if my config is handled correctly?**

**The Open Source Litmus Test**

If you post your entire codebase publicly, and was accessible to anyone in the world, would you be in trouble?

If you’ve stored passwords and API keys in your code, you’d be in trouble, so, no, you haven’t handled your configs correctly.

Else if your code is clean, and doesn’t contain any sensitive information, then your configs are handled correctly, congrats!

### How do you handle your configs?

You store them in your environment (the workspace where you build your application). Store them in files like .env **not in** settings.json, as they can be accidentally uploaded to the internet for hackers to see (bet you don’t want that)

Also, avoid grouping settings like `Environment = Production` , `Environment = Development` . This method doesn’t scale cleanly, as more deploys of the apps you create, new environment names are required. Instead, have individual swithces for  `Database_URL`,  `OPENAI_API_KEY` .