FROM docker.m.daocloud.io/library/maven:3.9-eclipse-temurin-21 AS build
WORKDIR /workspace
COPY pom.xml .
RUN mvn -q -DskipTests dependency:go-offline
COPY src ./src
# 单元测试由 GitHub Actions 执行；镜像构建仅产出可运行制品，便于本地快速启动。
RUN mvn -q -Dmaven.test.skip=true package

FROM docker.m.daocloud.io/library/eclipse-temurin:21-jre
WORKDIR /app
COPY --from=build /workspace/target/alert-service-1.0.0.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
