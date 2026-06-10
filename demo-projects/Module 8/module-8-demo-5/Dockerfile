FROM openjdk:8-jre-alpine
EXPOSE 8080
RUN mkdir -p /usr/app
WORKDIR /usr/app
COPY ./target/java-maven-app-*.jar /usr/app/
ENTRYPOINT ["sh", "-c", "java -jar /usr/app/java-maven-app-*.jar"]
