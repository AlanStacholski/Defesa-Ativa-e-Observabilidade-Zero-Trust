# Estágio 1: Compilação do JAR usando Maven e JDK 21
FROM maven:3.9.6-amazoncorretto-21 AS build
WORKDIR /app
COPY . .
RUN mvn clean package -DskipTests

# Estágio 2: Execução leve da aplicação
FROM amazoncorretto:21
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]