package main

import (
	"github.com/haproxytech/models"
)

func (c *ZorpController) apiStartTransaction() error {
	version, errVersion := c.NativeAPI.Configuration.GetVersion("")
	if errVersion != nil || version < 1 {
		//silently fallback to 1
		version = 1
	}
	//log.Println("Config version:", version)
	transaction, err := c.NativeAPI.Configuration.StartTransaction(version)
	c.ActiveTransaction = transaction.ID
	return err
}

func (c *ZorpController) apiCommitTransaction() error {
	_, err := c.NativeAPI.Configuration.CommitTransaction(c.ActiveTransaction)
	return err
}

func (c *ZorpController) apiDisposeTransaction() {
	c.ActiveTransaction = ""
}

func (c ZorpController) backendsGet() (models.Backends, error) {
	return nil, nil
}

func (c ZorpController) backendGet(backendName string) (models.Backend, error) {
	_, backend, err := c.NativeAPI.Configuration.GetBackend(backendName, c.ActiveTransaction)
	if err != nil {
		return models.Backend{}, err
	}
	return *backend, nil
}

func (c ZorpController) backendCreate(backend models.Backend) error {
	return c.NativeAPI.Configuration.CreateBackend(&backend, c.ActiveTransaction, 0)
}

func (c ZorpController) backendEdit(backend models.Backend) error {
	return c.NativeAPI.Configuration.EditBackend(backend.Name, &backend, c.ActiveTransaction, 0)
}

func (c ZorpController) backendDelete(backendName string) error {
	return c.NativeAPI.Configuration.DeleteBackend(backendName, c.ActiveTransaction, 0)
}

func (c ZorpController) backendServerCreate(backendName string, data models.Server) error {
	return c.NativeAPI.Configuration.CreateServer(backendName, &data, c.ActiveTransaction, 0)
}

func (c ZorpController) backendServerEdit(backendName string, data models.Server) error {
	return c.NativeAPI.Configuration.EditServer(data.Name, backendName, &data, c.ActiveTransaction, 0)
}

func (c ZorpController) backendServerDelete(backendName string, serverName string) error {
	return c.NativeAPI.Configuration.DeleteServer(serverName, backendName, c.ActiveTransaction, 0)
}

func (c ZorpController) backendSwitchingRuleCreate(frontend string, rule models.BackendSwitchingRule) error {
	return nil
}

func (c ZorpController) backendSwitchingRuleDeleteAll(frontend string) {
	var err error
	for err == nil {
		err = c.NativeAPI.Configuration.DeleteBackendSwitchingRule(0, frontend, c.ActiveTransaction, 0)
	}
}

func (c ZorpController) frontendGet(frontendName string) (models.Frontend, error) {
	_, frontend, err := c.NativeAPI.Configuration.GetFrontend(frontendName, c.ActiveTransaction)
	return *frontend, err
}

func (c ZorpController) frontendEdit(frontend models.Frontend) error {
	return c.NativeAPI.Configuration.EditFrontend(frontend.Name, &frontend, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendBindCreate(frontend string, bind models.Bind) error {
	return c.NativeAPI.Configuration.CreateBind(frontend, &bind, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendBindEdit(frontend string, bind models.Bind) error {
	return c.NativeAPI.Configuration.EditBind(bind.Name, frontend, &bind, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendBindDelete(frontend string, bindName string) error {
	return c.NativeAPI.Configuration.DeleteBind(bindName, frontend, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendACLAdd(frontend string, acl models.ACL) error {
	return c.NativeAPI.Configuration.CreateACL("frontend", frontend, &acl, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendACLDelete(frontend string, index int64) error {
	return c.NativeAPI.Configuration.DeleteACL(index, "frontend", frontend, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendACLsGet(frontend string) (models.Acls, error) {
	_, acls, err := c.NativeAPI.Configuration.GetACLs("frontend", frontend, c.ActiveTransaction)
	return acls, err
}

func (c ZorpController) frontendHTTPRequestRuleDeleteAll(frontend string) {
	var err error
	for err == nil {
		err = c.NativeAPI.Configuration.DeleteHTTPRequestRule(0, "frontend", frontend, c.ActiveTransaction, 0)
	}
}

func (c ZorpController) frontendHTTPRequestRuleCreate(frontend string, rule models.HTTPRequestRule) error {
	return c.NativeAPI.Configuration.CreateHTTPRequestRule("frontend", frontend, &rule, c.ActiveTransaction, 0)
}

func (c ZorpController) frontendTCPRequestRuleDeleteAll(frontend string) {
	var err error
	for err == nil {
		err = c.NativeAPI.Configuration.DeleteTCPRequestRule(0, "frontend", frontend, c.ActiveTransaction, 0)
	}
}

func (c ZorpController) frontendTCPRequestRuleCreate(frontend string, rule models.TCPRequestRule) error {
	return c.NativeAPI.Configuration.CreateTCPRequestRule("frontend", frontend, &rule, c.ActiveTransaction, 0)
}
