FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

RUN apt update && \
    apt install -y tzdata && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone && \
    dpkg-reconfigure --frontend noninteractive tzdata && \
    apt install -y \
        wget build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev \
        libreadline-dev libffi-dev libsqlite3-dev libbz2-dev liblzma-dev parallel \
        software-properties-common ca-certificates gnupg git curl unzip expect subversion maven \
        openjdk-8-jdk \
        openjdk-11-jdk \
        openjdk-21-jdk && \
    apt clean && \
    rm -rf /var/lib/apt/lists/* && \
    wget https://www.python.org/ftp/python/3.12.11/Python-3.12.11.tgz && \
    tar -xvf Python-3.12.11.tgz && \
    cd Python-3.12.11 && \
    ./configure --enable-optimizations && \
    make && \
    make install && \
    cd .. && \
    rm Python-3.12.11.tgz && \
    ln -s /usr/local/bin/python3 /usr/local/bin/python && \
    ln -s /usr/local/bin/pip3 /usr/local/bin/pip && \
    rm -rf /var/lib/apt/lists/* && \
    update-alternatives --set java /usr/lib/jvm/java-21-openjdk-amd64/bin/java && \
    update-alternatives --set javac /usr/lib/jvm/java-21-openjdk-amd64/bin/javac

RUN mkdir -p /d4j && \
    mkdir -p /hej && \
    cd /d4j && \
    git clone https://github.com/rjust/defects4j.git && \
    cd defects4j && \
    ./init.sh && \
    export PATH=$PATH:`pwd`/framework/bin && \
    cd /hej && \
    git clone https://github.com/ASSERT-KTH/human-eval-java.git && \
    cpan -i String::Interpolate && \
    cpan -i DBI

ENV PATH="$PATH:/d4j/defects4j/framework/bin"

COPY requirements.txt /

RUN pip install --no-cache-dir -r /requirements.txt && \
    rm /requirements.txt

WORKDIR /app

CMD ["/bin/bash"]